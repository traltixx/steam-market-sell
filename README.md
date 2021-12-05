# My script for setting all items to marketplace.

Set's all items from inventory to Steam marketplace.

## Usage
1. Install [Python](https://www.python.org).
1. Install [pip](https://pip.pypa.io/en/stable/installation/).
1. Install [required packages](requirements.txt).
   
    `pip install -r requirements.txt`
2. Run script with Steam keys as arguments seperated by space.
   
    `python main.py <Steam username>`

3. Login to Steam account.
 
## Example output
```shell
python .\main.py <Steam username>
Enter password for '<Steam username>': 
Enter 2FA code: XXXXX
Setting items to marketplace...
         Steam Gems Gems
                 Not marketable!
         Booster Pack Warlock - Master of the Arcane Booster Pack
                Price without fees as cents: 7
                Set to marketplace!
         Hollow Knight Foil Trading Card False Knight (Foil)
                Price without fees as cents: 59
                Set to marketplace!
         Inscryption Trading Card The Woodcarver
                Price without fees as cents: 8
                Set to marketplace!
         Inscryption Trading Card The Bone Lord
                Price without fees as cents: 10
                Set to marketplace!
         Leisure Suit Larry - Wet Dreams Don't Dry Trading Card Anu
                Price without fees as cents: 2
                Set to marketplace!
         Marvel's Guardians of the Galaxy Trading Card Gamora (Trading Card)
                Price without fees as cents: 10
                Set to marketplace!
         Psychonauts in the Rhombus of Ruin Trading Card The Scientists' Findings
                Price without fees as cents: 3
                Set to marketplace!
         Resident Evil 2 Trading Card Key Visual 1
                Price without fees as cents: 7
                Set to marketplace!
         The Debut Collection Sticker Steam Blink
                 Not marketable!
All listed!
```