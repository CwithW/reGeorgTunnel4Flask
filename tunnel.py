#coding:utf8

from flask import current_app as app

#put these variables somewhere safe and reachable.
import sys
sys.tunnels = {}
sys.currentTunnelId = 0


@app.route("/proxy",methods=['GET','POST'])
def tunnel():
    #this function has to be self contained, or you will see errors like request is not defined.
    from flask import request as request,make_response as make_response,session as session
    import socket
    import errno
    import sys
    import traceback
    tunnels = sys.tunnels
    currentTunnelId = sys.currentTunnelId
    def myMakeResponse(text,headers):
        resp = make_response(text)
        for i in headers:
            resp.headers[i] = headers[i]
        return resp
    if(request.method == "GET"):
        return "Georg says, 'All seems fine'"
    if(request.method != "POST"):
        return "?"
    respHeaders = {}
    respHeaders['X-STATUS'] = 'OK'
    headers = request.headers
    cmd = headers.get("X-CMD")
    tid = int(request.cookies.get("tunnelid",-1))
    if(cmd == "CONNECT"):
        target = headers["X-TARGET"]
        port = int(headers["X-PORT"])
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            respHeaders['X-STATUS'] = 'FAIL'
            respHeaders['X-ERROR'] = 'Failed creating socket(is this possible for python?)'
            return myMakeResponse('',respHeaders)
        try:
            sock.connect((target,port));
        except Exception as e:
            respHeaders['X-STATUS'] = 'FAIL'
            respHeaders['X-ERROR'] = 'Failed connecting to target'
            return myMakeResponse('',respHeaders)
        sock.setblocking(0)
        tunnels[currentTunnelId] = sock
        respHeaders['X-STATUS'] = 'OK'
        resp = myMakeResponse('',respHeaders)
        resp.set_cookie("tunnelid",str(currentTunnelId))
        sys.currentTunnelId+=1;
        return resp;    
    elif(cmd == "DISCONNECT"):
        try:
            tunnels[tid].close();
            del tunnels[tid];
        except:
            pass
        resp = myMakeResponse('',respHeaders)
        resp.set_cookie("tunnelid","-1")
        return resp;
    elif(cmd == "READ"):
        sock = tunnels[tid];
        try:
            buf = b""
            try:
                t = sock.recv(1024)
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    return myMakeResponse('',respHeaders)
                raise
            while t:
                buf += t
                try:
                    t = sock.recv(1024)
                except socket.error as e:
                    err = e.args[0]
                    if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                        break
                    raise
            resp = myMakeResponse(buf,respHeaders)
            return resp;
        except Exception as e:
            respHeaders['X-STATUS'] = 'FAIL'
            respHeaders['X-ERROR'] = str(e)
            return myMakeResponse('',respHeaders)
    elif(cmd == "FORWARD"):
        sock = tunnels[tid];
        try:
            readlen = int(request.headers["Content-Length"])
            buff = request.stream.read(readlen)
            sock.send(buff)
            respHeaders['X-STATUS'] = 'OK'
            return myMakeResponse('',respHeaders)
        except Exception as e:
            respHeaders['X-STATUS'] = 'FAIL'
            respHeaders['X-ERROR'] = str(e)
            return myMakeResponse('',respHeaders)
        