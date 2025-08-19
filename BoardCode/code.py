import board
import busio
import sdcardio
import storage

spi = board.SPI()
cs = board.D10

separator = ','
mount_point = '/sd'




mount_sd()