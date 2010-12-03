import celery

def main():
    from celery.bin import celeryd
    celeryd.main()

if __name__ == '__main__':
    main()

