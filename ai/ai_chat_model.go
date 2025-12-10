package ai

import (
	"context"

	"github.com/liliang-cn/ollama-go"
)

func Ai(message string) string {
	ctx := context.Background()
	messages := []ollama.Message{
		{Role: "user", Content: message},
	}
	response, err := ollama.Chat(ctx, "tars", messages)
	if err != nil {

	}
	return response.Message.Content

}
