from crtsh import crtshAPI
from pprint import pprint
from dns import resolver

all_hosts = []
certs = crtshAPI().search('DOMAIN_TO_SEARCH')
for cert in certs[0]:
  all_hosts.append(cert['name_value'])

hosts = set(all_hosts)

for host in hosts:
  try:
    a = resolver.query(host)
    print("{0}: {1}".format(host, a.canonical_name))
  except:
    print("{0} failed".format(host))
