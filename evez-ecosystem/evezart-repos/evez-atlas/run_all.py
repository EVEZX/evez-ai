import demo
import quantum


def main():
    print("Running demo...")
    demo.main()
    print("Helper availability:", ", ".join(quantum.__all__))


if __name__ == "__main__":
    main()
