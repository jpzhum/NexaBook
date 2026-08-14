# AI integration

OpenAI is an optional final provider, never the primary bibliographic source. It is enabled only when `ENABLE_OPENAI_FALLBACK=true` and an API key is present.

The provider receives an ISBN and a bounded instruction requesting a JSON object with the public `BookMetadata` fields. The response is parsed as JSON and validated by Pydantic. Invalid JSON, unexpected structure or SDK response errors result in no candidate; previously collected API metadata remains intact.

The public tests inject a fake Responses API client. They verify the structured result and fail-closed behavior without making paid network requests.

The model must not determine operational prices, permissions, authentication, or other sensitive business decisions.
