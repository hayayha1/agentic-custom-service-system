import asyncio
import httpx

async def test_get_doc():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8001") as client:
        # login as admin
        login_res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # test get doc
        doc_id = "268fa1c3-fe6f-4ee9-b17a-651992b5ab9e"
        res = await client.get(f"/api/v1/documents/{doc_id}", headers=headers)
        print("Status:", res.status_code)
        print("Data:", res.json())

        # login as ops
        login_ops = await client.post("/api/v1/auth/login", json={"username": "ops", "password": "ops123"})
        ops_token = login_ops.json()["token"]
        ops_headers = {"Authorization": f"Bearer {ops_token}"}
        res_ops = await client.get(f"/api/v1/documents/{doc_id}", headers=ops_headers)
        print("Ops Status:", res_ops.status_code)
        if res_ops.status_code == 200:
            print("Ops Content preview:", res_ops.json().get("content", "")[:100])
        else:
            print("Ops Error:", res_ops.text)

if __name__ == "__main__":
    asyncio.run(test_get_doc())
