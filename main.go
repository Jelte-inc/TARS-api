package main

import (
	"fmt"
	"net/http"

	"tars-api/ai"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return true }, // laat alle origins toe
}

func handleWS(w http.ResponseWriter, r *http.Request) {
	conn, _ := upgrader.Upgrade(w, r, nil) // upgrade HTTP -> WS
	defer conn.Close()

	for {
		// lees bericht van client
		_, msg, err := conn.ReadMessage()
		if err != nil {
			break
		}
		fmt.Println("Ontvangen:", string(msg))

		ai.AiModel(string(msg))

		// stuur het terug (echo)
		conn.WriteMessage(websocket.TextMessage, msg)
	}
}

func main() {
	http.HandleFunc("/ws", handleWS)
	fmt.Println("WebSocket-server draait op ws://localhost:8080/ws")
	http.ListenAndServe(":8080", nil)
}
