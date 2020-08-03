<p align="center">
	<a href="https://github.com/jerrylum/.25share"><img src="https://i.imgur.com/SZTjDWl.png" alt="IntroIcon" width="100"></a>
</p>
<h3 align="center">QuarterShare</h3>
<p align="center">
Quarter Share is made to enable easy message communication between mobile phones and computers. <br><br>
This project is divided into two parts, server (this repository) and mobile application
(<a href="https://github.com/jerrylum/.25share-android">here</a>). Pay a visit to our wiki page for more information about setup and usage.
</p>

<h4 align="center"><a href="https://github.com/jerrylum/topmost2/releases">Setup Now</a></h4>

---

### Have a quick look

Click the connect button. Then type something on your phone and send it.

<h5 align="left">
<img src="https://i.imgur.com/SAdyYWm.gif">
</h5>

<br>

### Is it dangerous?

The connection between the phone and the computer is secured with AES 256bit Encryption. By default, each new connection needs to be manually confirmed on the server to allow the client to send messages. Also, you can kick any clients you want.

<h5 align="left">
<img src="https://i.imgur.com/4S9r4R0.gif">
</h5>
<br>

### Configuration?

Sure! You can control how the server handles your messages using internal commands.

<h5 align="left">
<img src="https://i.imgur.com/0iSVWNZ.gif">
</h5>

<br>


### Other Features

- Computers and mobile phones can send messages in both directions
- Support multiple lines
- Quick connection speed
- Offline compatibility
- Command-line support
- Internal commands can be used within the server 
- Single Python script



---

### Wait! I am using Windows and/or iPhone!

You can check out [One Share](https://github.com/Jerrylum/OneShare). 


### Why I want to make Quarter Share?

The reason is very simple, just because I like voice input on the phone. For me, typing Chinese on the computer is a bit difficult.  

Now the voice input method on the computer is very complicated, and it is still not as convenient as the input method on the mobile phone. I invented this program so that I can use the phone’s voice input method to type on the computer.  

If you are using other input methods that can only be used on mobile phones, you can also use this program on your computer.

---

### Details / Not very fun fact

Each time the server is turned on, a new pair of RSA encryption keys will be created.  

When a client connects to the server, the server will send its public key to the client. After that, the client will generate an AES key and pass it with RSA public key encryption to the server. Then, the server decrypts the message and obtains the AES key. Finally, the server and the client can start encrypted communication.  

The security code is a MD5 hash value. Both the server and client will generate a security code using the RSA public key from the server and the AES key. To ensure the messages are secured, You need to verify that the security code displayed on the server is exactly the same as the one displayed on the client.

The server does not save any logs or configuration files to your computer.  


#### More snapshots


<img src="https://i.imgur.com/oeJoQ0M.png">


<img src="https://i.imgur.com/sgTCEC8.png">




### Command Line

```

usage: .25share [-h] [--host HOST] [--port PORT] [-a] [-f FLAG]    

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           The server's hostname or IP address
  --port PORT           The port to listen on
  -a, --allow           Allow all clients to send messages to the server
                        without the user's permission
  -f FLAG, --flag FLAG  mode flag

```


### Internal Command

```
.help                            show this help message
.flag                            show how the server handles messages
.chflag [flag]                   change how the server handles messages
.ls                              list all connected clients
.allow <client>                  allow client(s) to send messages
.kick <client>                   kick specified client(s)
.send <client> <content>         send a message to client(s)
.stop                            stop the server
```
    
#### Client Selector
```
@a      all clients
@p      the latest client who sent a message / connected
<ID>    specified client id, e.g. `5`
```

For example, using `.kick @a` command will kick all connected clients, using `.kick 30` command will kick a connected client with id **30**.

    
#### Note
1. Commands must be preceded by a period.
2. Any input that does not start with a period is understood as sending
the entire sentence to the latest client (@p).
3. If you want to send a message that starts with a period, use command 
`.send @p YOUR MESSAGE`

### Mode Flag

When you press the "Send" button on your phone to send a message, what should the server do after receiving it

```
p       Print on the console
s1      Copy to primary selection
s2      Copy to secondary selection
s3      Copy to clipboard
t       Typing text
```

You can use multiple flags at the same time. e.g. `t`, `s1`, `ps1` and `ps1s2t` are acceptable.  

It should look like this:
```
.25share -f ps1s2t            # command line
.chflag ps1s2t                # internal command
```


---

### Setup

Please go to [the wiki page](https://github.com/jerrylum/.25share/wiki).  

<br>

### Special Thanks

Thanks you [SamNg](https://github.com/ngkachunhlp) and [COMMANDER.WONG](https://github.com/COMMANDERWONG) for their suggestions and software testing.