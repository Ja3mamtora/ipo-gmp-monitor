import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import os 
# CREDENTIALS - Uses environment variables in production, hardcoded for local testing
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'your_email@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'your_app_password_here')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'recipient_email@gmail.com')

print(f"🔐 Email Configuration:")
print(f"   Sender: {SENDER_EMAIL}")
print(f"   Recipient: {RECIPIENT_EMAIL}")
print(f"   Password: {'*' * len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 'NOT SET'}")
print()

def send_email(subject, body, to_email):
    """Send email notification"""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        print(f"\n📧 Attempting to send email...")
        print(f"   From: {SENDER_EMAIL}")
        print(f"   To: {to_email}")
        
        # Using Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False

def check_ipo_gmp():
    """Scrape IPO data and check conditions"""
    url = "https://www.investorgain.com/report/live-ipo-gmp/331/close/"
    
    print("="*80)
    print(f"🔍 Starting IPO GMP check at {datetime.now()}")
    print(f"🌐 URL: {url}")
    print("="*80)
    
    try:
        # Try with Selenium for JavaScript-rendered content
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from webdriver_manager.chrome import ChromeDriverManager
            
            print("\n🌐 Using Selenium to fetch JavaScript-rendered content...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Use webdriver-manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get(url)
            
            # Wait for table to load
            print("⏳ Waiting for table to load...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "report_table"))
            )
            
            time.sleep(3)  # Additional wait for data to populate
            
            page_source = driver.page_source
            driver.quit()
            
            print("✅ Page loaded with Selenium")
            
        except ImportError:
            print("⚠️  Selenium not installed, falling back to requests...")
            print("💡 Install with: pip install selenium")
            print("💡 Also need ChromeDriver: https://chromedriver.chromium.org/")
            
            # Fallback to requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            page_source = response.content
            print(f"✅ Page fetched with requests (Status: {response.status_code})")
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find the specific table with ID
        table = soup.find('table', id='report_table')
        
        if not table:
            print("❌ Table with ID 'report_table' not found")
            print("\n🔍 Looking for any tables...")
            all_tables = soup.find_all('table')
            print(f"Found {len(all_tables)} table(s)")
            if len(all_tables) > 0:
                table = all_tables[0]
                print("✅ Using first table found")
            else:
                return
        else:
            print(f"✅ Table 'report_table' found")
        
        # Find tbody
        tbody = table.find('tbody')
        if not tbody:
            print("❌ No tbody found in table")
            return
        
        # Parse table rows from tbody
        rows = tbody.find_all('tr')
        print(f"\n📊 Total data rows found: {len(rows)}")
        print(f"📊 Processing rows...\n")
        
        matching_ipos = []
        
        # Process each row
        for row_num, row in enumerate(rows, 1):
            cols = row.find_all('td')
            if len(cols) < 2:
                continue
            
            print(f"\n{'─'*80}")
            print(f"ROW {row_num}:")
            print(f"{'─'*80}")
            
            # Get all column data
            name_col = cols[0] if len(cols) > 0 else None
            gmp_col = cols[1] if len(cols) > 1 else None
            rating_col = cols[2] if len(cols) > 2 else None
            sub_col = cols[3] if len(cols) > 3 else None
            
            # Print all columns
            for i, col in enumerate(cols):
                label = col.get('data-label', f'Column {i}')
                text = col.get_text(strip=True)
                print(f"  {label}: {text}")
            
            if not name_col:
                print("  ⏭️  Skipped: No name column")
                continue
            
            # Get IPO name
            name_link = name_col.find('a')
            if name_link:
                ipo_name = name_link.get_text(strip=True)
            else:
                ipo_name = name_col.get_text(strip=True)
            
            print(f"\n  🏷️  IPO Name: '{ipo_name}'")
            print(f"  ✓  Ends with 'IPO'? {ipo_name.endswith('IPO')}")
            
            # Check if name ends with "IPO"
            if not ipo_name.endswith('IPO'):
                print(f"  ⏭️  Skipped: Name doesn't end with 'IPO'")
                continue
            
            # Check for CT or C badge
            badges = name_col.find_all('span', class_='badge')
            badge_texts = [badge.get_text(strip=True) for badge in badges]
            has_ct = 'CT' in badge_texts or 'C' in badge_texts
            
            print(f"  🏅 Badges found: {badge_texts}")
            print(f"  🏅 Has CT/C badge? {has_ct}")
            
            if not has_ct:
                print(f"  ⏭️  Skipped: No CT/C badge found")
                continue
            
            # Get GMP value from GMP column
            gmp_value = None
            if gmp_col:
                gmp_text = gmp_col.get_text(strip=True)
                print(f"  💹 GMP Column Text: '{gmp_text}'")
                
                # Extract percentage from text like "₹97 (9.11%)"
                if '(' in gmp_text and '%' in gmp_text:
                    try:
                        # Extract percentage between parentheses
                        percentage_part = gmp_text.split('(')[1].split(')')[0]
                        percentage_str = percentage_part.replace('%', '').strip()
                        gmp_value = float(percentage_str)
                        print(f"  💹 Extracted GMP string: '{percentage_str}'")
                        print(f"  💹 Converted to float: {gmp_value}")
                        print(f"  💹 Type: {type(gmp_value)}")
                    except (IndexError, ValueError) as e:
                        print(f"  ⚠️  Could not parse GMP: {e}")
            
            if gmp_value is None:
                print(f"  ⚠️  No valid GMP value found")
                continue
            
            print(f"  📊 Comparison: {gmp_value} >= 13.0 ?")
            print(f"  ✓  GMP >= 13%? {gmp_value >= 13.0}")
            
            if gmp_value >= 13.0:
                matching_ipos.append({
                    'name': ipo_name,
                    'gmp': gmp_value
                })
                print(f"  ✅ MATCH FOUND! Adding to alert list")
            else:
                print(f"  ⏭️  Skipped: GMP ({gmp_value}%) is less than 13%")
        
        # Summary
        print(f"\n{'='*80}")
        print(f"📊 SUMMARY:")
        print(f"{'='*80}")
        print(f"Total IPOs processed: {len(rows)}")
        print(f"Matching IPOs found: {len(matching_ipos)}")
        
        # Send email if matches found
        if matching_ipos:
            print(f"\n🎯 Found {len(matching_ipos)} matching IPO(s):")
            for ipo in matching_ipos:
                print(f"   • {ipo['name']} - {ipo['gmp']}%")
            
            send_notification(matching_ipos)
        else:
            print(f"\n❌ No matching IPOs found (GMP >= 13% with CT badge)")
            
    except Exception as e:
        print(f"\n❌ Error checking IPO GMP: {str(e)}")
        import traceback
        traceback.print_exc()

def send_notification(ipos):
    """Send email with matching IPO details"""
    subject = f"🚀 IPO Alert: {len(ipos)} IPO(s) with GMP >= 13%"
    
    body = f"""
    <html>
    <body>
        <h2>IPO GMP Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
        <p>The following IPO(s) meet your criteria (GMP >= 13% with CT badge):</p>
        <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse;">
            <tr style="background-color: #f2f2f2;">
                <th>IPO Name</th>
                <th>GMP %</th>
            </tr>
    """
    
    for ipo in ipos:
        body += f"""
            <tr>
                <td>{ipo['name']}</td>
                <td><strong style="color: green;">{ipo['gmp']}%</strong></td>
            </tr>
        """
    
    body += """
        </table>
        <br>
        <p><small>This is an automated alert from your IPO GMP monitor.</small></p>
    </body>
    </html>
    """
    
    send_email(subject, body, RECIPIENT_EMAIL)

if __name__ == "__main__":
    check_ipo_gmp()
    print(f"\n{'='*80}")
    print(f"✅ Check completed at {datetime.now()}")
    print(f"{'='*80}")
