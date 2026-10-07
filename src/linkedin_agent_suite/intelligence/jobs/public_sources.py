"""Public remote job scrapers for Remotive and RemoteOK."""

import httpx

from ...core.models import Job


class PublicJobSources:
    @staticmethod
    async def fetch_remotive(limit: int = 10) -> list[Job]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get("https://remotive.com/api/remote-jobs?limit=10")
                if res.status_code == 200:
                    jobs_data = res.json().get("jobs", [])
                    return [
                        Job(
                            id=f"remotive-{j['id']}",
                            title=j["title"],
                            company=j["company_name"],
                            url=j["url"],
                            description=j.get("description", ""),
                            tags=j.get("tags", []),
                            source="remotive",
                        )
                        for j in jobs_data[:limit]
                    ]
        except Exception:
            pass
        return []

    @staticmethod
    async def fetch_remoteok(limit: int = 10) -> list[Job]:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get("https://remoteok.com/api", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    jobs_data = [
                        item for item in data if isinstance(item, dict) and "id" in item
                    ]
                    return [
                        Job(
                            id=f"remoteok-{j['id']}",
                            title=j.get("position", "Engineer"),
                            company=j.get("company", "Company"),
                            url=j.get("url", "https://remoteok.com"),
                            description=j.get("description", ""),
                            tags=j.get("tags", []),
                            source="remoteok",
                        )
                        for j in jobs_data[:limit]
                    ]
        except Exception:
            pass
        return []
