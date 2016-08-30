"""
Adapted from
http://arxiv.org/help/api/examples/python_arXiv_parsing_example.txt

with modifications by Alex Breitweiser

This is free software.  Feel free to do what you want
with it, but please play nice with the arXiv API!
"""

base_cat = "quant-ph"
cross_cats = {"cond-mat.str-el", "cond-mat.mes-hall"}

import urllib.request, urllib.parse, urllib.error
import feedparser
from datetime import date, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Base api query url
base_url = 'http://export.arxiv.org/api/query?';

# Search parameters
yesterday = date.today() - timedelta(1)
dby = yesterday - timedelta(1)
start_date = dby.strftime("%Y%m%d")+"2000"
end_date = yesterday.strftime("%Y%m%d") + "2000"
search_query = 'cat:%s+AND+lastUpdatedDate:[%s+TO+%s]' % (base_cat,
							  start_date,
							  end_date)
start = 0                     # retreive the first 5 results
max_results = 50

query = 'search_query=%s&start=%i&max_results=%i' % (search_query,
                                                     start,
                                                     max_results)

# Opensearch metadata such as totalResults, startIndex, 
# and itemsPerPage live in the opensearch namespase.
# Some entry metadata lives in the arXiv namespace.
# This is a hack to expose both of these namespaces in
# feedparser v4.1
feedparser._FeedParserMixin.namespaces['http://a9.com/-/spec/opensearch/1.1/'] = 'opensearch'
feedparser._FeedParserMixin.namespaces['http://arxiv.org/schemas/atom'] = 'arxiv'

# perform a GET request using the base_url and query
response = urllib.request.urlopen(base_url+query).read()

# parse the response using feedparser
feed = feedparser.parse(response)

title = "New %s submissions cross listed on %s" % (base_cat, ", ".join(cross_cats))

body = "<h1>%s</h1>" % (title)

body += 'Feed last updated: %s' % feed.feed.updated

# Run through each entry, and print out information
for entry in feed.entries:
    all_categories = [t['term'] for t in entry.tags]
    if not any(cat in cross_cats for cat in all_categories):
        continue
    arxiv_id = entry.id.split('/abs/')[-1]
    if arxiv_id[-2:] != 'v1':
        continue
    pdf_link = ''
    for link in entry.links:
        if link.rel == 'alternate':
            continue
        elif link.title == 'pdf':
            pdf_link = link.href
    body += '<a href="%s"><h2>%s</h2></a>' % (pdf_link, entry.title)
    
    # feedparser v5.0.1 correctly handles multiple authors, print them all
    try:
        body += 'Authors:  %s</br>' % ', '.join(author.name for author in entry.authors)
    except AttributeError:
        pass
    
    try:
        comment = entry.arxiv_comment
    except AttributeError:
        comment = 'No comment found'
    body += 'Comments: %s</br>' % comment
    
    # Since the <arxiv:primary_category> element has no data, only
    # attributes, feedparser does not store anything inside
    # entry.arxiv_primary_category
    # This is a dirty hack to get the primary_category, just take the
    # first element in entry.tags.  If anyone knows a better way to do
    # this, please email the list!
    body += 'Primary Category: %s</br>' % entry.tags[0]['term']
    
    # Lets get all the categories
    all_categories = [t['term'] for t in entry.tags]
    body += 'All Categories: %s</br>' % (', ').join(all_categories)
    
    # The abstract is in the <summary> element
    body += '<p>%s</p>' %  entry.summary
    body += '</br>'
print(body)


'''
email = "foo@bar.com"
password = "f00bar!"
msg = MIMEMultipart()
msg['Subject'] = title
msg['From'] = email
msg['To'] = email
msg.attach(MIMEText(body, 'html'))

smtp_host = 'smtp.gmail.com'
smtp_port = 587
server = smtplib.SMTP()
server.connect(smtp_host,smtp_port)
server.ehlo()
server.starttls()
server.login(email,password)
server.sendmail(user,tolist,msg.as_string())
'''
