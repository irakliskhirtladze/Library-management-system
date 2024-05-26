def fetch_all_pages(session, url, headers):
    results = []
    while url:
        response = session.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results.extend(data.get('results', []))
            url = data.get('next')
        else:
            break
    return results
