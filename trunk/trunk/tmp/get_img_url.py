import httplib

conn = httplib.HTTP('www.info-ufr.univ-montp2.fr:3128')

conn.putrequest('GET',"http://species.wikimedia.org/wiki/Pan")

conn.putheader('Accept', 'text/html')
conn.putheader('Accept', 'text/plain')


conn.endheaders()

errcode, errmsg, headers = conn.getreply()


f=conn.getfile()

for line in f.readlines():
    if "thumbinner" in line:
        #url_img = line.split("thumbinner")[1].split("href=\"")[1].split("\"")[0].strip()
        #print "http://species.wikimedia.org"+url_img
        url_img = line.split("thumbinner")[1].split("<img")[1].split("src=\"")[1].split("\"")[0].strip()
        print url_img
    conn.close()
