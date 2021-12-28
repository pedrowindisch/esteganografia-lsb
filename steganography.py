import cv2
import argparse
from enum import Enum

class SteganographyAction(Enum):
    ENCODE = "encode"
    DECODE = "decode"

    def __str__(self):
        return self.value

parser = argparse.ArgumentParser(description="Implementação de esteganorafia com LSB")

parser.add_argument(
    "action", 
    type=SteganographyAction,
    choices=list(SteganographyAction), 
    help="Define se o programa de esconder uma informação, ou tentar ler uma informação escondida.")

parser.add_argument(
    "file",
    help="O arquivo a ser utilizado no processo")

parser.add_argument(
    "--message",
    help="A mensagem a ser escondida."
)

parser.add_argument(
    "--out-file",
    help="O arquivo a ser salvo após esconder a informação. Se a opção não estiver presente, considera-se o nome do arquivo fornecido, prefixado de 'steg-', para salvar o resultado."
)

class SteganographyException(Exception):
    pass

class Steganography:
    PixelXPosition = 0
    PixelYPosition = 1

    def __init__(self, image):
        self.image = image

        self.image_width = image.shape[0]
        self.image_height = image.shape[1]
        self.qnty_image_channels = image.shape[2]

        self.current_pixel = (0, 0) 
        self.current_channel = 0

        self.message_to_encode = None
        self.out_file = None

    # Considera-se unidade como um espaço disponível para salvar informaçao
    def next_unit(self):
        # Se for possível, pula pro próximo canal de cor do pixel atual
        # Se não, pula pro próximo pixel
        if self.current_channel < self.qnty_image_channels - 1:
            self.current_channel += 1
        else:
            self.current_channel = 0
            
            # Se estiver na última coluna de pixels, pula pra próxima linha
            has_to_jump_to_new_row = self.current_pixel[Steganography.PixelXPosition] == self.image_width - 1
            
            if has_to_jump_to_new_row:
                self.current_pixel = (0, self.current_pixel[Steganography.PixelYPosition] + 1)
            else:
                self.current_pixel = (self.current_pixel[Steganography.PixelXPosition] + 1, self.current_pixel[Steganography.PixelYPosition]) 

    def get_current_slot_value(self):
        return self.image[self.current_pixel][self.current_channel]

    def set_current_slot_value(self, new_value):
        self.image[self.current_pixel][self.current_channel] = new_value

    def read_byte(self):
        byte = bin(int(self.image[self.current_pixel][self.current_channel]))
        self.next_unit()

        return byte

    def write_bit(self, bit):
        if not isinstance(bit, int): 
            bit = int(bit)

        current_channel_value = self.get_current_slot_value()
        
        if bit == 0:
            new_channel_value = current_channel_value & ~1
        else:
            new_channel_value = current_channel_value | 1

        self.set_current_slot_value(new_channel_value)
        self.next_unit()

    def write_byte(self, byte: str):
        if byte[:2] == "0b":
            byte = byte[2:]

        byte = byte.zfill(8)

        for bit in byte: self.write_bit(bit)

    # Verifica se a quantidade de pixels da imagem
    # é suficiente para esconder toda a informação
    def check_image_size(self, length):
        qnty_available_slots = self.image_width * self.image_height * self.qnty_image_channels
        
        return length <= qnty_available_slots

    def encode_image(self):
        if not self.check_image_size(len(self.message_to_encode)):
            raise SteganographyException("The value to be encoded is larger than allowed (the quantity of pixels of the image is not sufficient to allocate the message).")

        # Adiciona a quantidade de caracteres da mensagem
        # a ser encodada no começo da imagem.
        # Serve para delimitar quantos pixels ler
        # quando "decodar" a imagem 
        # self.write_byte(bin(len(value)))

        for byte in self.message_to_encode.encode():
            byte_as_string = bin(byte)
            self.write_byte(byte_as_string)

    def decode_image(self):
        decoded_message = ""

        for i in range(5):
            current_char = ""
            for i in range(8):
                current_char += self.read_byte()[-1]
            decoded_message += chr(int(current_char, 2))

        return decoded_message

    def save_image(self):
        cv2.imwrite(
            filename=self.out_file, 
            img=self.image
        )


if __name__ == "__main__":
    args = vars(parser.parse_args())

    if args["action"] == SteganographyAction.ENCODE and args["message"] is None:
        parser.error("Para esconder uma informação, é necessário prover uma mensagem com a flag --message")

    image = cv2.imread(filename=args["file"])
    steg = Steganography(image)

    if args["out_file"]: steg.out_file = args["out_file"]
    else: steg.out_file = "steg-" + args["file"]

    if args["action"] == SteganographyAction.ENCODE:
        
        steg.message_to_encode = args["message"] 
        steg.encode_image()
        steg.save_image()
    else:
        decoded_message = steg.decode_image()
        print(decoded_message)