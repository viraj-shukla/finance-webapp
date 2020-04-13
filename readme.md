The CS50 Finance web app for PSET 8, implemented by Viraj Shukla during the summer of 2019.

Setup:
1. Extract the zip file.
2. Ideally, the app will be running on the CS50 IDE (https://ide.cs50.io/).
   If running on a local computer, Python 3.7, Flask, SQLAlchemy must be downloaded, and modifications to the import statements may need to be made.
3. Run the following commands:
	$ cd PATH_TO_FINANCE
	$ export API_KEY=pk_872ed2a293824a41be8dba0384402532
4. In the PATH_TO_FINANCE folder (application.py must be in the current directory), run the app with the following command:
	$ flask run

Usage:
The app is meant to be a rudimentary stock manager, with stock values pulled in real time from IEX.
- Users can register and login to their own accounts, each of which starts with $10,000 of fake money.
- Quote: Get the current price of a stock symbol.
- Buy: Buy a select number of shares of a stock symbol.
- Sell: Sell a select number of shares among the stocks currently held by the user.
- History: Displays transaction history.

Specification: https://cs50.harvard.edu/x/2020/tracks/web/finance/
