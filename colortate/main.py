def main():
    import argparse

    ap = argparse.ArgumentParser()

    ap.add_argument("--headless", action="store_true",
            help="read new adjustment values from files and re-write the updated versions")

    ap.add_argument("filenames", nargs="+",
            help="css files to read/write.")

    args = ap.parse_args()

    from rotator import ColorRotator

    if args.headless:
        cr = ColorRotator(args.filenames)
        cr.write_files()

    else:
        import sys
        from gui import ColorRotatorWindow, QApplication

        app = QApplication(sys.argv, not args.headless)
        w = ColorRotatorWindow(args.filenames)
        w.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
