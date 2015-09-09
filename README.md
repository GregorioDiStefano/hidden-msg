# HiddenMsg
Hide data in PNG images by flipping the LSB values in each pixels RGB value.

# Explaination
Alice and Bob would like to talk in a secure manner (think pgp) over an insecure channel, but, they also dont want to attract the attention of nosey Carol.

They decide to hide their messages in a unsuspicious images they send one another. Unknowingly to Carol, these images actually contain encrypted data. 

Using lossless PNG/webp images, pixel colors can be slightly (lsb) modified to obfuscate a data payload.
