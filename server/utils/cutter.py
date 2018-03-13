


class Scissors(object):
    def __init__(self):
        self.default_size = 102400 # 100k

    def cut(self, raw_string, size=self.default_size):
        data_lst = []

        p, m = divmod(len(raw_string), size)
        page = p + 1 if m else p 

        for i in range(page):
            if i+1 == page:
                # The last page
                data = raw_string[i*size:]
            else:
                data = raw_string[i*size:(i+1)*size]

            data_lst.append({'page':page ,'index':i, 'data':data})

        return data_lst


class Sewing(object):
    def sew(self, data_lst):
        sorted_lst = sorted(data_lst, key=lambda dct: dct['index'])
        pieces_lst = [dct.get('data') for dct in sorted_lst]
        raw_string = reduce(lambda piece_1,piece_2: piece_1+piece_2, pieces_lst)

        return raw_string

