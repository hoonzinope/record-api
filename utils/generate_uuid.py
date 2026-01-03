# create uuid
import uuid
class GenerateUUID:
    @staticmethod
    def get() -> str:
        return str(uuid.uuid4())

if __name__ == "__main__":
    generator = GenerateUUID()
    print(generator.get())
