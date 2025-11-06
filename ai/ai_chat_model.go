package ai

import (
	"context"
	"fmt"
	"log"

	"github.com/liliang-cn/ollama-go"
)

func Ai(userInput string) {
	ctx := context.Background()
	if userInput == "bye bye" {
		return
	}
	model := "tars"

	messages := []ollama.Message{
		{Role: "user", Content: userInput},
	}
	responseChan, errChan := ollama.ChatStream(ctx, model, messages)

	for {
		select {
		case resp, ok := <-responseChan:
			if !ok {
				return
			}
			fmt.Print(resp.Message.Content)
		case err := <-errChan:
			if err != nil {
				log.Fatal("Error tijdens stream:", err)
			}
			return
		}
	}
}
