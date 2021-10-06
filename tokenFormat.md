## Token format

Base64url encoded "train-cars". 
+ Cars are separated by periods. 
+ There is always the required engine car that specifies the user/server.
+ Trailing are the forms of auth, in order of recomended preference.
+ Minimize whitespace characters on encode to save space

### "Engine" (Required)
```json
{
    "typ" : "engine",
    "hsvr":"blackline.xyz",
    "user":"@exmpl:blackline.xyz"
}
```

### "valid token" car
Not to be confused with the `m.login.token` login method. This is a live session on the server
The expiery is a unix time int. Set to 0 for never expire.
```json
{
    "typ" : "valid-token",
    "token" : "alidhfrgb_ASDFajhsd-ddd",
    "exp" : 1633238196,
    "device_id" : "Halcyon Bot"
}
```

### "username and password" car
```json
{
    "typ" : "password",
    "un" : "@exmpl:blackline.xyz",
    "pw" : "bundle0fOranges"
}
```