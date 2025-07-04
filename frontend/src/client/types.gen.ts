// This file is auto-generated by @hey-api/openapi-ts

export type FunctionRequest = {
  language: string
  body: string
}

export type FunctionResponse = {
  id: string
  language: string
  url: string
  created_at: string
}

export type HTTPValidationError = {
  detail?: Array<ValidationError>
}

export type ValidationError = {
  loc: Array<string | number>
  msg: string
  type: string
}

export type CreateFunctionFunctionsPostData = {
  requestBody: FunctionRequest
}

export type CreateFunctionFunctionsPostResponse = FunctionResponse

export type DeleteFunctionFunctionsFunctionIdDeleteData = {
  functionId: string
}

export type DeleteFunctionFunctionsFunctionIdDeleteResponse = unknown
