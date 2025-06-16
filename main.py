from llm.callLlama import CallLlama

def main():
    while(True) :
        print("hello sir! celestial here.. how may i of help today")
        prompt = input("prompt : ").strip()
        llama = CallLlama("llama3-gradient")
        print(llama.askLlama(prompt))


if __name__ == "__main__":
    main()