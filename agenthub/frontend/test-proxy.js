fetch('/api/agents', {
  headers: { 'X-API-Key': 'dev-secret-key' },
})
  .then((r) => r.json())
  .then((d) => console.log('Success:', d))
  .catch((e) => console.error('Error:', e))
