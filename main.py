# Argument parsing.
from argparse import ArgumentParser

# Authenticating with steam.
from steam.webauth import WebAuth

# Making calls with session.
from requests import Session

# Load JSON to dict.
from json import loads,dumps

# Get ceil and floor mathemical functions.
from math import ceil, floor

# Handle regex.
import re

import random
import time
import traceback

# Init argument parser.
parser: ArgumentParser = ArgumentParser()
# Add Steam username as required argument.
parser.add_argument("username", type=str, help="Your Steam username.")

# Init with given Steam username.
user: WebAuth = WebAuth(parser.parse_args().username)
del parser

# Login with command line and init session.
session: Session = user.cli_login()

# Url for Steam Comminity.
URL_STEAM_COMMINITY: str = "https://steamcommunity.com"

# User's Steam ID.
ID_STEAM: int = user.steam_id.as_64

# Get wallet info from HTML.
g_rgWalletInfo: dict = loads(
    re.search(
        r"var g_rgWalletInfo = {.*}",
        session.get(f"{URL_STEAM_COMMINITY}/profiles/{ID_STEAM}/inventory/").text,
        re.ASCII,
    )[0].split("=")[1]
)


SELL_MODE = True

def price_without_fees_as_cents(with_fees: float, description: dict) -> int:
    """Price without fees as cents.
    Uses Steam's javascript functions as base.

    Args:
        with_fees (float): Price with fees.
        description (dict): Item data.

    Returns:
        int: Price without fees as cents.
    """
    # Get with fees as cents integer.
    mAmount: int = ceil(with_fees * 100)
    # Return value with fees with fees removed.
    return mAmount - CalculateFeeAmount(
        mAmount,
        # Get market fee from description or wallet info.
        float(
            description["market_fee"]
            if "market_fee" in description
            else g_rgWalletInfo["wallet_publisher_fee_percent_default"]
        ),
    )


def CalculateFeeAmount(amount: int, publisherFee: float = 0.00) -> int:
    """Fee amount as cents.
    Uses Steam's javascript function CalculateFeeAmount as base.

    Args:
        amount (int): Price with fees.
        publisherFee (float, optional): Publisher fee. Defaults to 0.00.

    Returns:
        int:Fee amount as cents.
    """
    if "wallet_fee" not in g_rgWalletInfo or not g_rgWalletInfo["wallet_fee"]:
        return 0

    # Since CalculateFeeAmount has a Math.floor, we could be off a cent or two. Let's check:
    iterations = 0
    # shouldn't be needed, but included to be sure nothing unforseen causes us to get stuck
    nEstimatedAmountOfWalletFundsReceivedByOtherParty = int(
        (amount - int(g_rgWalletInfo["wallet_fee_base"]))
        / (float(g_rgWalletInfo["wallet_fee_percent"]) + publisherFee + 1)
    )

    bEverUndershot = False
    fees = CalculateAmountToSendForDesiredReceivedAmount(
        nEstimatedAmountOfWalletFundsReceivedByOtherParty, publisherFee
    )
    while fees["amount"] != amount and iterations < 10:
        if fees["amount"] > amount:
            if bEverUndershot:
                fees = CalculateAmountToSendForDesiredReceivedAmount(
                    nEstimatedAmountOfWalletFundsReceivedByOtherParty - 1, publisherFee
                )
                fees["steam_fee"] += amount - fees["amount"]
                fees["fees"] += amount - fees["amount"]
                fees["amount"] = amount
                break
            else:
                nEstimatedAmountOfWalletFundsReceivedByOtherParty -= 1
        else:
            bEverUndershot = True
            nEstimatedAmountOfWalletFundsReceivedByOtherParty += 1

        fees = CalculateAmountToSendForDesiredReceivedAmount(
            nEstimatedAmountOfWalletFundsReceivedByOtherParty, publisherFee
        )
        iterations += 1

    # fees.amount should equal the passed in amount
    return fees["fees"]


def CalculateAmountToSendForDesiredReceivedAmount(
    receivedAmount: int, publisherFee: float = 0.00
) -> dict:
    """Calculated fee data.

    Args:
        receivedAmount (int): Amount to receive.
        publisherFee (float, optional): Publisher fee. Defaults to 0.00.

    Returns:
        dict: Calculated fee data.
    """
    nSteamFee = int(
        floor(
            max(
                receivedAmount * float(g_rgWalletInfo["wallet_fee_percent"]),
                float(g_rgWalletInfo["wallet_fee_minimum"]),
            )
            + int(g_rgWalletInfo["wallet_fee_base"])
        )
    )
    nPublisherFee = int(
        floor(max(receivedAmount * publisherFee, 1) if publisherFee > 0 else 0)
    )
    nAmountToSend = receivedAmount + nSteamFee + nPublisherFee

    return {
        "steam_fee": nSteamFee,
        "publisher_fee": nPublisherFee,
        "fees": nSteamFee + nPublisherFee,
        "amount": int(nAmountToSend),
    }

def find_name(datadict,assetinfo):
    result = ""
    classid = assetinfo["classid"]
    instanceid = assetinfo["instanceid"]
    for description in datadict["descriptions"]:
        if classid == description["classid"] and instanceid == description["instanceid"]:
            return description["market_hash_name"]
    return result

def find_description(datadict,assetinfo):
    result = {}
    classid = assetinfo["classid"]
    instanceid = assetinfo["instanceid"]
    for description in datadict["descriptions"]:
        if classid == description["classid"] and instanceid == description["instanceid"]:
            return description
    return result

# Id for app "Steam".
ID_APP: int = 440
# Id for context "Community".
ID_CONTEXT: int = 2
# Language for data.
LANGUAGE = "english"



# Get inventory data.
data: dict = session.get(
    f"{URL_STEAM_COMMINITY}/inventory/{ID_STEAM}/{ID_APP}/{ID_CONTEXT}",
    params={
        "l": LANGUAGE,
    },
).json()
#del LANGUAGE

# Map classid to asset data.
classid_to_asset: dict = {}    
for asset in data["assets"]:
    classid_to_asset[asset["classid"]] = asset

# Country code for "Australia".
COUNTRY: str = "AU"

# Currency "Australian Dollars".
CURRENCY: int = 21
# Regex to get float parts from currency string.
#CURRENCY_REGEX: str = r"^(?P<integer>[0-9])+,(?P<fractional>[0-9]{2})€$" #euro regex
CURRENCY_REGEX: str = r"^A\$ (?P<integer>[0-9])+\.(?P<fractional>[0-9]{2})" #aus dollar regex

# Url for price overview.
URL_PRICEOVERVIEW = f"{URL_STEAM_COMMINITY}/market/priceoverview/"

# Id for session.
ID_SESSION: str = user.session_id
#del user

# Url for selling item.
URL_SELLITEM = f"{URL_STEAM_COMMINITY}/market/sellitem/"

# Headers for selling item.
HEADERS: dict = {"Referer": f"{URL_STEAM_COMMINITY}/profiles/{ID_STEAM}/inventory"}
#del URL_STEAM_COMMINITY
#del ID_STEAM

#change/modify this to the name of the things you want to sell
sell_names = ["Winter 2020 War Paint Case","Unleash the Beast Cosmetic Case","Mann Co. Supply Munition Series #103","Mayflower Cosmetic Case","Mann Co. Supply Munition Series #90","Ghoulish Gains Case","Fall 2013 Gourd Crate Series #73","Mann Co. Strongbox Series #81","Fall 2013 Acorns Crate Series #72","Enchantment: Eternaween","Mann Co. Supply Crate Series #77","Mann Co. Supply Crate Series #75","Mann Co. Supply Crate Series #71","Mann Co. Supply Munition Series #82","Mann Co. Supply Munition Series #84","Mann Co. Supply Munition Series #90","Scream Fortress XII War Paint Case","Spooky Spoils Case","Summer 2019 Cosmetic Case","Scream Fortress XIV War Paint Case","Wicked Windfall Case"]

selling = []
# Loop assets.
pause = random.randint(1,5) # we want to pause to not overload steam and not trigger any of their automated systems
print("Selling items to marketplace...in "+str(pause)+" seconds")
for asset in data["assets"]:
    itemname = find_name(data,asset)
    if itemname in sell_names:
        print("Selling "+itemname)
        time.sleep(pause)
        description = find_description(data,asset)

        # Get priceoverview for item.
        priceoverview: dict = session.get(
            URL_PRICEOVERVIEW,
            params={
                "country": COUNTRY,
                "currency": CURRENCY,
                "appid": ID_APP,
                "market_hash_name": itemname,
            },
        ).json()     

        # Getting priceoverview failed.
        if "success" not in priceoverview or not priceoverview["success"]:
            raise Exception("priceoverview failed!", priceoverview)

        #print(priceoverview)
        # Get integer and fractional from currency string.
        parts = re.search(CURRENCY_REGEX, priceoverview["lowest_price"])
        #print(parts)
        del priceoverview
        integer: str = parts.group("integer")
        fractional: str = parts.group("fractional")
        del parts

        # Generate price from integer and factorional.
        price: float = float(f"{integer}.{fractional}")
        del integer
        del fractional

        # If price was 0 or less
        if price <= 0.00:
            print("\t\tPrice was 0 or less!")
            # move to next.
            continue

        # Get price without fees as cents.
        price_without_fees_cents = price_without_fees_as_cents(price, description)
        print(
            "\t\tPrice without fees as cents:",
            price_without_fees_cents,
        )
        del description
        del price
        

        # Sell item.
        if SELL_MODE:
            try:
                sellitem: dict = session.post(
                    URL_SELLITEM,
                    data={
                        "sessionid": ID_SESSION,
                        "appid": ID_APP,
                        "contextid": ID_CONTEXT,
                        "assetid": asset["assetid"],
                        "amount": asset["amount"],
                        "price": price_without_fees_cents,
                    },
                    headers=HEADERS,
                ).json()
                del asset
                del price_without_fees_cents

                # Check if sale succeeded.
                if "success" not in sellitem or not sellitem["success"]:
                    raise Exception("sellitem failed!", sellitem)
                del sellitem
                print("\t\tSet to marketplace!")
            except:
                print(traceback.format_exc())
                
                
                
del session
del g_rgWalletInfo
del ID_APP
del ID_CONTEXT
del classid_to_asset
del COUNTRY
del CURRENCY
del CURRENCY_REGEX
del URL_PRICEOVERVIEW
del ID_SESSION
print("All listed!")

# Exit with success.
exit(0)
