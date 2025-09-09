claude mcp add n8n-mcp \
  -e MCP_MODE=stdio \
  -e LOG_LEVEL=error \
  -e DISABLE_CONSOLE_OUTPUT=true \
  -e N8N_API_URL=https://n8n.isolarpv.cz \
  -e N8N_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwNTU4MDBhYi02NTc4LTRhYWYtOWQzNC0yMTU3Y2Q0NjViYTIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU2ODMwNTk2fQ.sjml6tLPVRs8i4Ff4sER8_Inq7mm4Fdfm4NlG_cVlzI \
  -- npx n8n-mcp