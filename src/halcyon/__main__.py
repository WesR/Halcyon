from .halcyon import *
import argparse

if __name__ == "__main__":
    client = Client()

    parser = argparse.ArgumentParser(prog='halcyon',
        description='By this, you can generate a halcyonToken for your project, \
        for example python3 -m halcyon -H matrix.org -u @kevin:matrix.org -p on&on&on1337',
        epilog="Have fun creating")
    parser.add_argument('-s', '--server', help='Homeserver the user belongs to ex: matrix.org')
    parser.add_argument('-u', '--username', help='Your full username ex: @kevin:matrix.org')
    parser.add_argument('-p', '--password', help='Your full password for your matrix account')
    parser.add_argument('--include-password', action="store_true", help='Save your username and password in the token for reauth (Not required right now since matrix tokens do not expire)')

    parser.add_argument('--decode', help='Decode an existing token that you pass in')
    parser.add_argument('--pretty', action="store_true", help='Pretty print the decoded token')
    parser.add_argument('--revoke', help='Revoke an existing token')
    parser.add_argument('--revoke-all-tokens', help='Revoke an all existing tokens for the account')

    args = parser.parse_args()

    if args.decode:
        splitToken = args.decode.split(".")
        if args.pretty:
            [print(json.dumps(client._decodeTokenDict(x), indent=2)) for x in splitToken]
        else:
            [print(json.dumps(client._decodeTokenDict(x))) for x in splitToken]
        exit()


    if args.revoke:
        splitToken = args.revoke.split(".")
        for x in splitToken:
            decodedToken = client._decodeTokenDict(x)
            #We assume that the engine payload is always first... 
            if decodedToken["typ"] == "engine":
                client.restrunner = restrunner.Runner(homeserver=decodedToken["hsvr"])

            if decodedToken["typ"] == "valid-token":
                client.restrunner.access_token = decodedToken["token"]
                if client._logoutUser() == {}:
                    print("Token revoked")
                exit()

    if args.revoke_all_tokens:
        splitToken = args.revoke_all_tokens.split(".")
        for x in splitToken:
            decodedToken = client._decodeTokenDict(x)
            if decodedToken["typ"] == "engine":
                client.restrunner = restrunner.Runner(homeserver=decodedToken["hsvr"])

            if decodedToken["typ"] == "valid-token":
                client.restrunner.access_token = decodedToken["token"]
                resp = client._logoutUser(revokeAllTokens=True)
                if resp == {}:
                    print("Tokens revoked")

                print(resp)
                exit()

    if not args.server:
        print("Please specify a homeserver")
        exit()
    else:
        client.restrunner = restrunner.Runner(homeserver=args.server)

    if args.username and args.password:
        halcyonToken = str()#final token
        
        halcyonToken += client._encodeTokenDict({
                "typ" : "engine",
                "hsvr" : args.server,
                "user" : args.username
            })

        newSessionToken = client._generateNewSessionToken(args.username, args.password)
        halcyonToken += "." + client._encodeTokenDict({
                "typ" : "valid-token",
                "token" : newSessionToken["access_token"],
                "exp" : 0,#not a spec yet
                "device_id" : newSessionToken["device_id"]
            })

        print("Happy hacking!\n")
        print(halcyonToken)
    else:
        print("Please include a username and password")