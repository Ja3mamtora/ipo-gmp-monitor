import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

def send_email(subject, body, to_email):
    """Send email notification"""
    # Use environment variables for security
    from_email = os.environ.get('SENDER_EMAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        # Using Gmail SMTP - adjust if using different provider
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def check_ipo_gmp():
    """Scrape IPO data and check conditions"""
    url = "https://www.investorgain.com/report/live-ipo-gmp/331/all/"
    
    try:
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table
        table = soup.find('table')
        if not table:
            print("Table not found on the page")
            return
        
        matching_ipos = []
        
        # Parse table rows
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 2:
                continue
            
            # Get IPO name (first column)
            name_col = cols[0]
            ipo_name = name_col.get_text(strip=True)
            
            # Check if name ends with "IPO"
            if not ipo_name.endswith('IPO'):
                continue
            
            # Check for CT badge
            ct_badge = name_col.find('span', class_='badge rounded-pill bg-primary d-inline ms-2')
            if not ct_badge or 'CT' not in ct_badge.get_text():
                continue
            
            # Get GMP column (usually around 4th-6th column, adjust based on actual structure)
            # Look for GMP value - typically shown as percentage
            gmp_value = None
            for col in cols:
                text = col.get_text(strip=True)
                if '%' in text:
                    try:
                        # Extract percentage value
                        gmp_text = text.replace('%', '').replace('+', '').strip()
                        gmp_value = float(gmp_text)
                        break
                    except ValueError:
                        continue
            
            if gmp_value is not None and gmp_value >= 13:
                matching_ipos.append({
                    'name': ipo_name,
                    'gmp': gmp_value
                })
                print(f"Found matching IPO: {ipo_name} with GMP: {gmp_value}%")
        
        # Send email if matches found
        if matching_ipos:
            send_notification(matching_ipos)
        else:
            print(f"No matching IPOs found at {datetime.now()}")
            
    except Exception as e:
        print(f"Error checking IPO GMP: {str(e)}")

def send_notification(ipos):
    """Send email with matching IPO details"""
    to_email = os.environ.get('RECIPIENT_EMAIL')
    
    subject = f"🚀 IPO Alert: {len(ipos)} IPO(s) with GMP >= 13%"
    
    body = f"""
    <html>
    <body>
        <h2>IPO GMP Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
        <p>The following IPO(s) meet your criteria (GMP >= 13% with CT badge):</p>
        <table border="1" cellpadding="10" cellspacing="0">
            <tr>
                <th>IPO Name</th>
                <th>GMP %</th>
            </tr>
    """
    
    for ipo in ipos:
        body += f"""
            <tr>
                <td>{ipo['name']}</td>
                <td><strong>{ipo['gmp']}%</strong></td>
            </tr>
        """
    
    body += """
        </table>
        <p><small>This is an automated alert from your IPO GMP monitor.</small></p>
    </body>
    </html>
    """
    
    send_email(subject, body, to_email)

if __name__ == "__main__":
    print(f"Starting IPO GMP check at {datetime.now()}")
    check_ipo_gmp()
    print("Check completed")