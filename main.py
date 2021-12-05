# Argument parsing.
from argparse import ArgumentParser

# Authenticating with steam.
from steam.webauth import WebAuth

# Making calls with session.
from requests import Session

# Load JSON to dict.
from json import loads

# Get ceil and floor mathemical functions.
from math import ceil, floor

# Handle regex.
import re


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


# Id for app "Steam".
ID_APP: int = 753
# Id for context "Community".
ID_CONTEXT: int = 6
# Language for data.
LANGUAGE = "english"

# Get inventory data.
data: dict = session.get(
    f"{URL_STEAM_COMMINITY}/inventory/{ID_STEAM}/{ID_APP}/{ID_CONTEXT}",
    params={
        "l": LANGUAGE,
    },
).json()
del LANGUAGE

# Map classid to asset data.
classid_to_asset: dict = {}
for asset in data["assets"]:
    classid_to_asset[asset["classid"]] = asset

# Country code for "Finland".
COUNTRY: str = "FI"

# Currency "Euro".
CURRENCY: int = 3
# Regex to get float parts from currency string.
CURRENCY_REGEX: str = r"^(?P<integer>[0-9])+,(?P<fractional>[0-9]{2})€$"

# Url for price overview.
URL_PRICEOVERVIEW = f"{URL_STEAM_COMMINITY}/market/priceoverview/"

# Id for session.
ID_SESSION: str = user.session_id
del user

# Url for selling item.
URL_SELLITEM = f"{URL_STEAM_COMMINITY}/market/sellitem/"

# Headers for selling item.
HEADERS: dict = {"Referer": f"{URL_STEAM_COMMINITY}/profiles/{ID_STEAM}/inventory"}
del URL_STEAM_COMMINITY
del ID_STEAM

print("Setting items to marketplace...")
# Loop descriptions.
for description in data["descriptions"]:
    # Print name.
    print("\t", description["type"], description["name"])

    # Was not marketable
    if description["marketable"] != 1:
        print("\t\t Not marketable!")
        # so skip.
        continue

    # Get asset data for classid.
    asset: dict = classid_to_asset[description["classid"]]

    # Get priceoverview for item.
    priceoverview: dict = session.get(
        URL_PRICEOVERVIEW,
        params={
            "country": COUNTRY,
            "currency": CURRENCY,
            "appid": ID_APP,
            "market_hash_name": description["market_hash_name"],
        },
    ).json()

    # Getting priceoverview failed.
    if "success" not in priceoverview or not priceoverview["success"]:
        raise Exception("priceoverview failed!", priceoverview)

    # Get integer and fractional from currency string.
    parts = re.search(CURRENCY_REGEX, priceoverview["lowest_price"])
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
