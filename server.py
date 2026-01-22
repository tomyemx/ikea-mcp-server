from mcp.server.fastmcp import FastMCP
import google.generativeai as genai

# הגדרת המפתח של גוגל
# הדבק את המפתח שלך בתוך הגרשיים למטה
MY_API_KEY = "AIzaSyAewiblc4puegt-Q8u1mWG73seCobt1Zi0"
genai.configure(api_key=MY_API_KEY)

# יצירת השרת בשם "IkeaAgent"
mcp = FastMCP("IkeaAgent")

# כלי דמה לבדיקה (עדיין לא סורק באמת)
@mcp.tool()
def search_sale_living_room_items(category: str) -> str:
    """
    Search for discounted living room items in IKEA Israel.
    Returns dummy data for testing.
    """
    print(f"Server is searching for: {category}")
    return "Test Result: Sofa KIVIK, 500 NIS"

if __name__ == "__main__":
    mcp.run()