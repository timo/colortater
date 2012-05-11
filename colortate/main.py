def main():
    import argparse

    ap = argparse.ArgumentParser()

    ap.add_argument("--headless", "-H", action="store_true",
            help="read new adjustment values from files and re-write the updated versions")

    ap.add_argument("--adjust", "-a", nargs=2, metavar=["representant", "value"], action="append",
            help="adjust the group belonging to representant by value.")

    ap.add_argument("--groups", "-g", action="store_true",
            help="display groups and their representants")

    ap.add_argument("filenames", nargs="+",
            help="css files to read/write.")

    args = ap.parse_args()

    from rotator import ColorRotator

    if args.headless:
        cr = ColorRotator(args.filenames)

        if args.groups:
            for group in cr.groups:
                print "%s: %s" % (group[0].name(), " ".join(map(lambda x:x.name(), group)))

        print args.adjust

        for representant, value in args.adjust or []:
            print "adjusting %s by %r" % (representant, value)
            value = int(value)
            if not cr.rotate_group(representant, value):
                print "  couldn't find group for %r" % (representant)

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
