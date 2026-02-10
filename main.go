package main

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"
	"sync"

	"example.com/m/ai"
	"github.com/gorilla/websocket"
)

// WebSocket upgrader
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true },
}

// AudioBuffer houdt audio op tot volledig bestand
type AudioBuffer struct {
	mu    sync.Mutex
	audio []byte
	done  bool
}

func (b *AudioBuffer) Append(chunk []byte) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.audio = append(b.audio, chunk...)
}

func (b *AudioBuffer) Get() []byte {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.audio
}

func (b *AudioBuffer) SetDone() {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.done = true
}

func (b *AudioBuffer) IsDone() bool {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.done
}

// WebSocket handler
func wsHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Println("Upgrade error:", err)
		return
	}
	defer conn.Close()

	buffer := &AudioBuffer{}

	for {
		msgType, data, err := conn.ReadMessage()
		if err != nil {
			log.Println("ReadMessage error:", err)
			break
		}

		if msgType == websocket.BinaryMessage {
			// audio chunk ontvangen
			buffer.Append(data)
		} else if msgType == websocket.TextMessage {
			text := string(data)
			if text == "end" {
				// hele audiofragment ontvangen
				buffer.SetDone()
				log.Println("Full audio received, processing...")

				go processAudio(buffer, conn)
			}
		}
	}

}

func splitIntoSentences(text string) []string {
	text = strings.TrimSpace(text)
	if text == "" {
		return nil
	}

	// Regex: splits op ., !, ? gevolgd door spatie of einde
	re := regexp.MustCompile(`(?m)([^.!?]+[.!?]?)`)
	matches := re.FindAllString(text, -1)

	var sentences []string
	for _, s := range matches {
		s = strings.TrimSpace(s)
		if s != "" {
			sentences = append(sentences, s)
		}
	}

	// fallback: hele tekst als 1 zin
	if len(sentences) == 0 {
		sentences = append(sentences, text)
	}

	return sentences
}

func addWavHeader(pcm []byte, sampleRate int, channels int, bitsPerSample int) []byte {
	byteRate := sampleRate * channels * bitsPerSample / 8
	blockAlign := channels * bitsPerSample / 8
	dataLen := len(pcm)
	riffLen := 36 + dataLen

	buf := &bytes.Buffer{}

	// RIFF header
	buf.WriteString("RIFF")
	binary.Write(buf, binary.LittleEndian, uint32(riffLen))
	buf.WriteString("WAVE")

	// fmt chunk
	buf.WriteString("fmt ")
	binary.Write(buf, binary.LittleEndian, uint32(16)) // PCM
	binary.Write(buf, binary.LittleEndian, uint16(1))  // AudioFormat = PCM
	binary.Write(buf, binary.LittleEndian, uint16(channels))
	binary.Write(buf, binary.LittleEndian, uint32(sampleRate))
	binary.Write(buf, binary.LittleEndian, uint32(byteRate))
	binary.Write(buf, binary.LittleEndian, uint16(blockAlign))
	binary.Write(buf, binary.LittleEndian, uint16(bitsPerSample))

	// data chunk
	buf.WriteString("data")
	binary.Write(buf, binary.LittleEndian, uint32(dataLen))
	buf.Write(pcm)

	return buf.Bytes()
}

// Simpele mock STT + AI pipeline
func processAudio(buffer *AudioBuffer, conn *websocket.Conn) {
	if !buffer.IsDone() {
		log.Println("Buffer nog niet klaar")
		return
	}
	audio := buffer.Get()

	filename := "received_audio.wav"
	wav := addWavHeader(audio, 16000, 1, 16)
	err := os.WriteFile("received_audio.wav", wav, 0644)
	if err != nil {
		log.Println("Fout bij opslaan bestand:", err)
		return
	}
	log.Println("Audio opgeslagen als", filename)
	resp, err := http.Get("http://localhost:8000/stt")
	fmt.Printf("resp", resp)
	// Hier zou je STT aanroepen (bijv. Whisper of Vosk)
	text, _ := io.ReadAll(resp.Body)
	type AiOutput struct {
		Command string   `json:"command"`
		Args    []string `json:"args"`
		Speech  string   `json:"speech"`
	}
	var aiOutputObj = AiOutput{}
	// AI vertaling / verwerking
	aiOutput := ai.Ai(string(text))
	cleanJSON := strings.ReplaceAll(aiOutput, "```json", "")
	cleanJSON = strings.ReplaceAll(cleanJSON, "```", "")
	cleanJSON = strings.TrimSpace(cleanJSON)
	err = json.Unmarshal([]byte(cleanJSON), &aiOutputObj)
	if err := conn.WriteMessage(websocket.TextMessage, []byte(cleanJSON)); err != nil {
		log.Println("WebSocket write error:", err)
	}
	fmt.Printf("AI-output:", aiOutputObj.Speech)
	sentences := splitIntoSentences(aiOutputObj.Speech)
	fmt.Print(sentences)
	for _, s := range sentences {
		sentence := map[string]string{
			"sentence": s,
		}
		data, err := json.Marshal(sentence)
		if err != nil {
			log.Fatal("Error encoding JSON:", err)
		}
		resp, err := http.Post("http://localhost:8000/tts", "application/json", bytes.NewBuffer(data))
		if err != nil {
			log.Fatal("Error sending POST request:", err)
		}
		audioData, err := io.ReadAll(resp.Body) // haal hele WAV in één keer op
		resp.Body.Close()
		if err != nil {
			log.Fatal(err)
		}
		if len(audioData) == 0 {
			log.Println("Waarschuwing: lege audio ontvangen van TTS")
			return
		}

		// Stuur alles in één WebSocket bericht
		if err := conn.WriteMessage(websocket.BinaryMessage, audioData); err != nil {
			log.Println("WebSocket write error:", err)
		}

		// Stuur einde van zin
		if err := conn.WriteMessage(websocket.TextMessage, []byte("end")); err != nil {
			log.Println("WebSocket write error:", err)
		}

		// Stuur een korte tekstmelding om einde van zin aan te geven
		if err := conn.WriteMessage(websocket.TextMessage, []byte("end")); err != nil {
			log.Println("WriteMessage error:", err)
			break
		}
	}

}

// Mock AI functie
func mockAI(transcript string) string {
	// Verwerk transcriptie (hier dummy)
	return fmt.Sprintf("AI output: %s", transcript)
}

var stdin io.WriteCloser
var scanner *bufio.Scanner

func main() {

	http.HandleFunc("/ws", wsHandler)
	log.Println("Server gestart op :8080")
	log.Fatal(http.ListenAndServe(":56277", nil))
}
