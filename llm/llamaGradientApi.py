from callLlama import CallLlama

def main():
    llama = CallLlama('llama3-gradient')
    response = llama.askLlama("hi celestial")
    print(response)

if __name__ == "__main__":
    main()
