# AI integration

OpenAI is an optional final provider, never the primary bibliographic source. It is enabled only when `ENABLE_OPENAI_FALLBACK=true` and an API key is present.

The provider receives an ISBN and a bounded instruction requesting a JSON object with the public `BookMetadata` fields. The response is parsed as JSON and validated by Pydantic. Invalid JSON, unexpected structure or SDK response errors result in no candidate; previously collected API metadata remains intact.

The implementation does not use JSON mode or native Structured Outputs. It asks for JSON in the prompt and validates the parsed response locally. The SDK client has an 8-second timeout and two retries.

The public tests inject a fake Responses API client. They verify the validated JSON result and fail-closed behavior without making paid network requests.

The model must not determine operational prices, permissions, authentication, or other sensitive business decisions.
