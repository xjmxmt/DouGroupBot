import random


class RespGen:
    def __init__(self):
        # self.bot = None
        self.map = {}
        # load responses
        # with open('words.txt', "r", encoding='utf-8') as file:
        #     lines = file.readlines()
        #     i = 0
            # while i < len(lines):
            #     titles = lines[i].strip().split('/')
            #     i += 1
            #     resps = []
            #     while len(lines[i].strip()) > 0:
            #         resps.append(lines[i].strip())
            #         i += 1
            #     for t in titles:
            #         self.map[t] = resps
            #
            #     while i < len(lines) and len(lines[i].strip()) <= 0:
            #         i += 1

            # while i < len(lines):
            #     self.map[str(i)] = lines[i].strip()
            #     i += 1

        # self.li = []
        # with open('', "r", encoding='utf-8') as file:
        #     lines = file.readlines()
        #     for l in lines:
        #         l = l.strip()
        #         if len(l) == 0:
        #             continue
        #         self.li.append(l)

        self.possibles = self.map.keys()

        self.resp_dict = {}
        with open('../resources/response.txt', 'r') as f:
            lines = f.readlines()
            i = 1
            for l in lines:
                l = l.strip()
                self.resp_dict[i] = {'res': l}
                i += 1

    # def getResp(self, ques: str, userID: str):
        # try:
        #     rsp = self.bot.getAnws(ques, userID)
        #     if len(rsp) > 0:
        #         return rsp
        # except AttributeError:
        #     pass

        # keyword = None
        # for match in self.possibles:
        #     if match in ques:
        #         keyword = match
        #         break
        # rsp = self.map.get(keyword)
        # if (rsp is not None):
        #     chosen = random.randint(0, len(rsp) - 1)
        #     return rsp[chosen]
        #
        # chosen = random.randint(0, len(self.li) - 1)
        # return self.li[chosen]

    def getResp(self):
        keys = list(self.resp_dict.keys())
        l = len(keys)
        i = random.randint(1, l)
        resp = self.resp_dict[i]
        resp['res'] = resp['res'] + ' '*random.randint(0, 20)
        return resp


if __name__ == '__main__':
    r = RespGen()
    rsp = r.getResp()
    print(rsp)