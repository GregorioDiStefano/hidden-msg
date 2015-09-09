# HiddenMsg
Steganography in lossless images

# Explaination
Alice and Bob would like to talk in a secure manner (think pgp) over an insecure channel, but, they also dont want to attract the attention of nosey Carol.

They decide to hide their messages in a unsuspicious images they send one another. Unknowingly to Carol, these images actually contain encrypted data. 

Using lossless PNG/webp images, pixel colors can be slightly (lsb) modified to obfuscate a data payload.
