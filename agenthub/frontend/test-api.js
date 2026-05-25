const apiUrl = 'http://localhost:7005'
const apiKey = 'dev-secret-key'

async function test() {
  const res = await fetch(`${apiUrl}/api/agents`, {
    headers: { 'X-API-Key': apiKey },
  })
  console.log('Status:', res.status)
  console.log('Data:', await res.json())
}

test()
