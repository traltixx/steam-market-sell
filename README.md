# My script for setting all items to marketplace.

Sell some crates from the TF2 inventory to Steam marketplace.
Crate names can be added to the sell_names variable in line 227

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
Selling items to marketplace...
Selling Unleash the Beast Cosmetic Case
                Price without fees as cents: 2
                Set to marketplace!
Selling Unleash the Beast Cosmetic Case
                Price without fees as cents: 2
                Set to marketplace!
Selling Unleash the Beast Cosmetic Case
                Price without fees as cents: 2
                Set to marketplace!
Selling Unleash the Beast Cosmetic Case
                Price without fees as cents: 2
                Set to marketplace!
Selling Unleash the Beast Cosmetic Case
                Price without fees as cents: 2
                Set to marketplace!
All listed!
```
