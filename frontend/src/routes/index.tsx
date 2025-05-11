import {
  Box,
  Button,
  Container,
  createListCollection,
  Flex,
  Heading,
  Portal,
  Select,
  Stack,
  Text,
  Textarea,
} from "@chakra-ui/react"
import useCustomToast from "@/hooks/useCustomToast"
import { useMutation } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import { DefaultService } from "@/client"

const SUPPORTED_LANGUAGES = ["python", "go"] as const
const languages = createListCollection({
  items: [
    { label: "Python", value: "python" },
    { label: "Go", value: "go" },
  ],
})
type Language = (typeof SUPPORTED_LANGUAGES)[number]

const DEFAULT_FUNCTION_BODY = `def handler(ctx):
    """
    This function is the entry point for the function.
    It will be invoked by the FaaS platform.
    """
    return {
        "statusCode": 200,
        "message": "Hello World"
    }`

export const Route = createFileRoute("/")({
  component: Home,
})

function Home() {
  const [selectedLanguage, setSelectedLanguage] = useState<Language>("python")
  const [functionBody, setFunctionBody] = useState(DEFAULT_FUNCTION_BODY)
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const createFunction = useMutation({
    mutationFn: (params: { language: string; body: string }) =>
      DefaultService.createFunctionFunctionsPost({
        requestBody: {
          language: params.language,
          body: params.body,
        },
      }),
    onSuccess: (data) => {
      showSuccessToast(`Function URL: ${data.url}`)
    },
    onError: (error) => {
      showErrorToast(error instanceof Error ? error.message : "Unknown error")
    },
  })

  return (
    <Container maxW="container.xl" py={8}>
      <Stack spacing={6}>
        <Box textAlign="center">
          <Heading size="2xl" mb={4}>
            Function as a Service Platform
          </Heading>
          <Text fontSize="lg" color="gray.600">
            Create and deploy serverless functions in multiple languages
          </Text>
        </Box>

        <Box p={6} borderWidth="1px" borderRadius="lg" bg="chakra-subtle-bg">
          <Stack spacing={4}>
            <Heading size="md">Create New Function</Heading>
            <Select.Root 
              collection={languages} 
              size="sm" 
              width="320px"
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value as Language)}
            >
              <Select.HiddenSelect />
              <Select.Label>Select Language</Select.Label>
              <Select.Control>
                <Select.Trigger>
                  <Select.ValueText placeholder="Select Language" />
                </Select.Trigger>
                <Select.IndicatorGroup>
                  <Select.Indicator />
                </Select.IndicatorGroup>
              </Select.Control>
              <Portal>
                <Select.Positioner>
                  <Select.Content>
                    {languages.items.map((language) => (
                      <Select.Item item={language} key={language.value}>
                        {language.label}
                        <Select.ItemIndicator />
                      </Select.Item>
                    ))}
                  </Select.Content>
                </Select.Positioner>
              </Portal>
            </Select.Root>

            <Textarea
              value={functionBody}
              onChange={(e) => setFunctionBody(e.target.value)}
              placeholder="Enter your function code here..."
              size="sm"
              minHeight="200px"
              fontFamily="monospace"
              spellCheck={false}
            />

            <Flex justify="flex-end">
              <Button
                colorScheme="teal"
                onClick={() =>
                  createFunction.mutate({
                    language: selectedLanguage,
                    body: functionBody,
                  })
                }
                isLoading={createFunction.isPending}
              >
                Create Function
              </Button>
            </Flex>
          </Stack>
        </Box>

        {createFunction.data && (
          <Box p={6} borderWidth="1px" borderRadius="lg" bg="chakra-subtle-bg">
            <Stack spacing={3}>
              <Heading size="sm">Latest Created Function</Heading>
              <Text>
                <strong>ID:</strong> {createFunction.data.id}
              </Text>
              <Text>
                <strong>Language:</strong> {createFunction.data.language}
              </Text>
              <Text>
                <strong>Created At:</strong>{" "}
                {new Date(createFunction.data.created_at).toLocaleString()}
              </Text>
              <Text>
                <strong>URL:</strong>{" "}
                <a href={createFunction.data.url} target="_blank" rel="noopener noreferrer">
                  {createFunction.data.url}
                </a>
              </Text>
            </Stack>
          </Box>
        )}
      </Stack>
    </Container>
  )
}

export default Home