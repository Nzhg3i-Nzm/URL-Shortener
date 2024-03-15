import mysql.connector
import http.server as httpserver
import socketserver
from getpass import getpass

connect = mysql.connector.connect(
    host = "localhost",
    user = input("Enter MYSQL Username\n"),
    password = getpass("Enter MYSQL Password\n"),
)

mycursor = connect.cursor()

def sqlsetup():
    #sets up the sql db if not already configured
    mycursor.execute("CREATE DATABASE IF NOT EXISTS urlshortener")
    mycursor.execute("USE urlshortener")
    mycursor.execute("CREATE TABLE IF NOT EXISTS urls(ID int NOT NULL, url varchar(255) NOT NULL, PRIMARY KEY (ID));")
    connect.commit()

def addURL(url):
    #gets current length of items in table, adds next one to table
    mycursor.execute("SELECT COUNT(*) FROM urls")
    count = mycursor.fetchall()
    ID = int(count[0][0])+1
    existingID = getIDByURL(url)
    mycursor.execute("INSERT INTO urls (ID, url) VALUES(%s, %s)", (str(ID), url) )
    connect.commit()

def getIDByURL(url):
    mycursor.execute("SELECT ID FROM urls WHERE url=%s", (url,) )
    ID = mycursor.fetchall()
    if len(ID)==0:
        return ''
    else:
        ID = int(ID[0][0])
        return ID

def getURLByID(ID):
    mycursor.execute("SELECT url FROM urls WHERE ID=%s", (str(ID),) )
    url = mycursor.fetchall()
    if len(url)==0:
        return ''
    else:
        return url[0][0]

def removeXSS(url):
    bad_chars = ['\'', '\"', '$', '*', '(', ')', '=', '{', '}', '[', ']', '|', '\\', ';', '<', '>', ',', '+']
    url_enc = ["%27", "%22", "%24", "%2A", "%28", "%29", "%3D", "%7B", "%7D", "%5B", "%5D", "%7C", "%5C", "%3B", "%3C", "%3E", "%2C", "%20"]
    i=0
    san_url = url
    while i<len(bad_chars):
        san_url = san_url.replace(bad_chars[i], url_enc[i])
        i+=1
    return san_url

def parseURL(url):
    if url.find("https://")==0:
        url = url[8:]
    elif url.find("http://")==0:
        url = url[7:]
    return url

def server():
    class SimpleHTTPRequestHandler(httpserver.SimpleHTTPRequestHandler):
        def do_GET(self):
            if '?' in self.path:
                ID = self.path[self.path.find('?')+1:]
                url = getURLByID(int(ID))
                if url=='':
                    self.wfile.write(bytes("error, invalid URL", "utf-8"))
                else:
                    self.send_response(200)
                    self.send_header('Content-type','text/html')
                    self.end_headers()
                    self.wfile.write(bytes("<html><head></head><body><script>window.location=\"http://"+removeXSS(url)+"\"</script></body></html>", "utf-8"))
            elif self.path == "/":
                self.path = "/home.html"
            return httpserver.SimpleHTTPRequestHandler.do_GET(self)
        def do_POST(self):
            if self.path == "/api/addurl":
                url = self.headers["url"]
                p_url = parseURL(url)
                
                existingID = getIDByURL(p_url)
                if existingID == '':
                    print(p_url)
                    addURL(p_url)
                    self.send_response(200)
                    self.send_header('Content-type','text/plain')
                    self.end_headers()
                    self.wfile.write(bytes(str(getIDByURL(p_url)), "utf-8"))
                else:
                    self.send_response(200)
                    self.send_header('Content-type','text/plain')
                    self.end_headers()
                    self.wfile.write(bytes(str(existingID), "utf-8"))
    handler_object = SimpleHTTPRequestHandler
    PORT = 8000
    myserver = httpserver.HTTPServer(("", PORT), handler_object)
    print("Serving http://localhost:"+str(PORT))
    myserver.serve_forever()

def main():
    sqlsetup()
    server()

main()
