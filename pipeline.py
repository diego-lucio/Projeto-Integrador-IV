import subprocess, sys
from dotenv import load_dotenv

def run_cmd(cmd):
    print('\n$ ' + ' '.join(cmd) + '\n')
    p = subprocess.run(cmd, check=False)
    if p.returncode != 0:
        sys.exit(p.returncode)

def main():
    load_dotenv()
    run_cmd([sys.executable, 'scripts/etl_cetesb.py'])
    run_cmd([sys.executable, 'scripts/etl_inmet.py'])

if __name__ == '__main__':
    main()
