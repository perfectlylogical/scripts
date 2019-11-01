import requests
import cloudpassage
from bs4 import BeautifulSoup

api_key = "cloud_passage_api_key"
api_secret = "cloud_passage_api_secret"

session = cloudpassage.HaloSession(api_key, api_secret)
issues = cloudpassage.Issue(session)
issue_list = issues.list_all()


all_cves = {}
for issue in issue_list:
  if issue['issue_type'] == 'sva':
    if issue['package_name'] != all_cves:
      all_cves[issue['package_name']] = []
    for cve in issue['cve_ids']:
      all_cves[issue['package_name']].append(cve)

for package in all_cves:
  all_cves[package] = sorted(set(all_cves[package]))
  # Query the Ubuntu site for the cve
  for cve in all_cves[package]:
    url = 'https://people.canonical.com/~ubuntu-security/cve/{0}/{1}.html'.format(cve.split("-")[1],cve)
    resp = requests.get(url)
    page = BeautifulSoup(resp.content, 'html.parser')
    tables = page.findAll(lambda tag: tag.name=='table')
    for table in tables
      for row in table.findAll("tr"):
        # Check if the package is patched in Ubuntu 16.04
        if "16.04" in str(row):
          columns = row.find_all('td')
          print("{0},{1},{2}".format(package,cve,columns[1].find_next('span').get_text()))
