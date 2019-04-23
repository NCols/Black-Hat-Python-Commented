#!/usr/bin/env python
# -*- coding: utf-8 -*-

# We have to first import the IBurpExtender class, which is a requirement
# for every extension we write. We follow this up by importing our
# necessary classes for creating an Intruder payload generator.
from burp import IBurpExtender
from burp import IIntruderPayloadGeneratorFactory
from burp import IIntruderPayloadGenerator

from java.util import List, ArrayList

import random

# Next we define our BurpExtender class, which extends the IBurpExtender and IIntruderPayloadGeneratorFactory classes
class BurpExtender(IBurpExtender, IIntruderPayloadGeneratorFactory):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        # We then use the registerIntruderPayloadGeneratorFactory function
        # to register our class so that the Intruder tool is aware that we can generate payloads
        callbacks.registerIntruderPayloadGeneratorFactory(self)

        return

    # We implement the getGeneratorName function to simply return the name of our payload generator
    def getGeneratorName(self):
        return "BHP Payload Generator"

    # The last step is the createNewInstance function that receives the attack
    # parameter and returns an instance of the IIntruderPayloadGenerator class, which we called BHPFuzzer.
    def createNewInstance(self, attack):
        return BHPFuzzer(self, attack)

class BHPFuzzer(IIntruderPayloadGenerator):
    # We define the required class variables as well as
    # add max_payloads and num_iterations variables so that we can keep track
    # of when to let Burp know we’re finished fuzzing.
    def __init__(self, extender, attack):
        self._extender = extender
        self._helpers = extender._helpers
        self._attack = attack
        self.max_payloads = 10
        self.num_iterations = 0

        return

    # We implement the hasMorePayloads function that simply checks
    # whether we have reached the maximum number of fuzzing iterations
    def hasMorePayloads(self):
        if self.num_iterations == self.max_payloads:
            return False
        else:
            return True

    # The getNextPayload function is the one that receives the original HTTP
    # payload and it is here that we will be fuzzing
    def getNextPayload(self, current_payload):
        # The current_payload variable arrives as a byte array, so we convert this to a string
        # and then pass it to our fuzzing function mutate_payload
        payload = "".join(chr(x) for x in current_payload)

        # Call our simple mutator to fuzz the POST
        payload = self.mutate_payload(payload)

        # Increase the number of fuzzing attempts
        self.num_iterations += 1

        # And return the payload
        return payload

    def reset(self):
        self.num_iterations = 0
        return

    """
    Now let’s drop in the world’s simplest fuzzing function that you can
    modify to your heart’s content. Because this function is aware of the cur-
    rent payload, if you have a tricky protocol that needs something special, like
    a CRC checksum at the beginning of the payload or a length field, you can
    do those calculations inside this function before returning, which makes it
    extremely flexible.
    """

    def mutate_payload(self, original_payload):
        # Pick a simple mutator or even call an external script
        picker = random.randint(1,3)

        # Select a random offset in the payload to mutate
        offset = random.randint(0, len(original_payload)-1)
        payload = original_payload[:offset]

        # Random offset insert a SQL injection attempt
        if picker == 1:
            payload += "'"

        # Jam an XSS attemps in
        if picker == 2:
            payload += "<script>alert('BHP!');</script>"

        # Repeat a chunk of the original payload a random number
        if picker == 3:
            chunk_length = random.randint(len(payload[offset:]),len(payload)-1)
            repeater = random.randin(1,10)

            for i in range(repeater):
                payload += original_payload[offset:offset+chunk_length]

        # Add the remaining bits of the payload
        payload += original_payload[offset:]

        return payload
