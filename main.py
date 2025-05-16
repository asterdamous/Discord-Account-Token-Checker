import requests
import asyncio
import argparse
import logging
import os
import sys
from datetime import datetime
from colorama import init, Fore, Style
import json

init()

DEFAULT_TOKEN_FILE = 'Token.txt'
DEFAULT_OUTPUT_FILE = f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'

logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_token_validity(token):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers)
        if response.status_code == 200:
            userinfo = response.json()
            
            user_id = userinfo.get("id")
            creation_timestamp = ((int(user_id) >> 22) + 1420070400000) / 1000
            creation_date = datetime.fromtimestamp(creation_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
            flags = userinfo.get('flags', 0)
            badges = []
            if flags & (1 << 0): badges.append("Discord Staff")
            if flags & (1 << 1): badges.append("Discord Partner")
            if flags & (1 << 2): badges.append("HypeSquad Events")
            if flags & (1 << 3): badges.append("Bug Hunter Level 1")
            if flags & (1 << 9): badges.append("Early Supporter")
            
            premium_type = "None"
            if userinfo.get("premium_type") == 1:
                premium_type = "Nitro Classic"
            elif userinfo.get("premium_type") == 2:
                premium_type = "Nitro"
            
            account_details = {
                'username': f"{userinfo['username']}#{userinfo['discriminator']}",
                'user_id': user_id,
                'email': userinfo.get('email', 'Not available'),
                'phone': userinfo.get('phone', 'Not available'),
                'verified': userinfo.get('verified', False),
                'creation_date': creation_date,
                'premium_type': premium_type,
                'badges': badges,
                'locale': userinfo.get('locale', 'Not available'),
                'avatar_url': f"https://cdn.discordapp.com/avatars/{user_id}/{userinfo.get('avatar')}.png" if userinfo.get('avatar') else "No avatar"
            }
            
            logger.info(f"{Fore.GREEN}Valid token found for user: {account_details['username']}{Style.RESET_ALL}")
            return True, account_details
        else:
            logger.warning(f"{Fore.RED}Invalid token: {token[:10]}... (Status Code: {response.status_code}){Style.RESET_ALL}")
            return False, {}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"{Fore.RED}Network Error: {str(e)}{Style.RESET_ALL}")
        return False, {}
    except Exception as e:
        logger.error(f"{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
        return False, {}

async def format_result(token, valid, details, index, total):
    status_color = Fore.GREEN if valid else Fore.RED
    status = "VALID" if valid else "INVALID"
    
    result = f"{status_color}Token: {token[:10]}... | Status: {status}{Style.RESET_ALL}"
    
    if valid:
        result += "\nDetails:"
        for key, value in details.items():
            if isinstance(value, list):
                result += f"\n  - {key}: {', '.join(value) if value else 'None'}"
            else:
                result += f"\n  - {key}: {value}"
    
    return result

async def process_tokens(tokens, output_file=None):
    results = []
    valid_count = 0
    invalid_count = 0
    
    print(f"\n{Fore.CYAN}Starting token validation...{Style.RESET_ALL}\n")
    
    for index, token in enumerate(tokens, 1):
        print(f"{Fore.YELLOW}Processing token {index}/{len(tokens)}{Style.RESET_ALL}")
        valid, details = await check_token_validity(token)
        
        if valid:
            valid_count += 1
        else:
            invalid_count += 1

        result = await format_result(token, valid, details, index, len(tokens))
        results.append(result)
        print(f"{result}\n")
        await asyncio.sleep(1)

    summary = f"""
{Fore.CYAN}=== All Tokens Check Summary ==={Style.RESET_ALL}
Total Tokens: {len(tokens)}
{Fore.GREEN}Valid Tokens: {valid_count}{Style.RESET_ALL}
{Fore.RED}Invalid Tokens: {invalid_count}{Style.RESET_ALL}
Success Rate: {(valid_count/len(tokens)*100):.2f}%
"""
    print(summary)
    results.append(summary)

    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(results))
            logger.info(f"{Fore.GREEN}Results saved to {output_file}{Style.RESET_ALL}")
        except IOError as e:
            logger.error(f"{Fore.RED}Failed to write output: {str(e)}{Style.RESET_ALL}")

    return results

def main():
    print(f"""{Fore.CYAN}
╔══════════════════════════════════════╗
║     Discord Token Checker v2.0       ║
║         MADE BY ASTERDAMOUS          ║
╚══════════════════════════════════════╝{Style.RESET_ALL}
""")

    parser = argparse.ArgumentParser(description='Advanced Discord Token Checker')
    parser.add_argument('-t', '--token', help='Single token to check')
    parser.add_argument('-i', '--input', help='File containing tokens', default=DEFAULT_TOKEN_FILE)
    parser.add_argument('-o', '--output', help='Output file for results', default=DEFAULT_OUTPUT_FILE)
    
    args = parser.parse_args()

    if not any([args.token, args.input]) and os.path.exists(DEFAULT_TOKEN_FILE):
        args.input = DEFAULT_TOKEN_FILE

    tokens = []
    if args.token:
        tokens.append(args.token)
    if args.input:
        try:
            with open(args.input, 'r') as f:
                tokens.extend(line.strip() for line in f if line.strip())
            logger.info(f"Loaded {len(tokens)} tokens from {args.input}")
        except FileNotFoundError:
            parser.error(f"Input file not found: {args.input}")

    if not tokens:
        parser.error("No tokens provided. Use -t for single token or -i for input file")

    asyncio.run(process_tokens(tokens, args.output))

if __name__ == "__main__":
    main()
