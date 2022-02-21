class UpdateCorsById(Command):
    def __init__(self):
        super().__init__()

    def get_options(self):
        return [
            Group(Option('-f', '--file', dest='json_file'),
                  Option('-j', '-json', dest='json_string'), exclusive=True)
        ]

    def run(self, json_file=None, json_string=None):
        if json_string is not None:
            json_data = json.loads(json_string)
        else:
            with open(json_file, 'r') as handler:
                json_data = json.load(handler)

        print('Start processing...\n')
        for line in json_data:
            if line.get('device_id') is None:
                raise ValueError("device_id field required")
            else:
                device_id = line.get('device_id')

            cors = Cors.query.filter_by(device_id=device_id).first()
            if cors is None:
                print(f'Cors with device_id {device_id} do not exist.')
                continue
            if line.get('base_code') is not None:
                cors.base_code = line['base_code']
            if line.get('gnss_serial') is not None:
                cors.gnss_serial = line['gnss_serial']
            if line.get('device_type') is not None:
                cors.device_type = line['device_type']
            if line.get('mpo_version') is not None:
                cors.mpo_version = line['mpo_version']
            cors.update_token()
            print(db.dirty)
        db.commit()


class AddCorsFromJson(Command):
    def __init__(self):
        super().__init__()

    def get_options(self):
        return [
            Group(Option('-j', '--json', dest='json_string'),
                  Option('-f', '--file', dest='file_path'), exclusive=True)
        ]

    def run(self, json_string=None, file_path=None):
        if json_string is not None:
            json_data = json.loads(json_string)
        else:
            with open(file_path) as handler:
                json_data = json.load(handler)

        broken_items = []
        new_items = []

        print('Start processing...\n')
        for line in json_data:
            try:
                if line.get('base_code') is None or line.get('base_code') == "":
                    raise ValueError("base_code field reuired")
                if line.get('device_type') is None or line.get('device_type') == "":
                    raise ValueError("device_type reuired")
                if line.get('gnss_serial') is None or line.get('gnss_serial') == "":
                    raise ValueError("gnss_serial field reuired")
                if line.get('mpo_version') is None or line.get('mpo_version') == "":
                    raise ValueError("mpo_version field reuired")
                if line.get('device_id') is None or line.get('device_id') == "":
                    raise ValueError("device_id field reuired")

                base_code = line['base_code'].strip()
                device_type = line['device_type'].strip()
                gnss_serial = line['gnss_serial'].strip()
                mpo_version = float(line['mpo_version'].strip())
                device_id = line['device_id'].strip()

                cors = Cors(base_code, gnss_serial, device_type, mpo_version, device_id)
                db.add(cors)
                new_items.append({str(cors),})
            # except AssertionError as e:
            #     print('BS: ', line.get('base_code'), '; reason: ', str(e))
            # except ValueError as e:
            except Exception as e:
                broken_items.append({'code':line.get('base_code'), 'reason': str(e)})
        print(f"Total json-items: {len(json_data)}\n")
        print(f"New corses: {len(new_items)}\n", new_items, '\n')
        print(f'Broken items: {len(broken_items)}\n', broken_items)

        print('Committing...')
        db.commit()

        print('Saving results to assets...')
        with open(os.path.join(os.path.dirname(file_path), 'broken_corses.json'), 'w') as handler:
            json.dump(broken_items, handler)


class AddProblemSource(Command):
    def __init__(self):
        super(AddProblemSource, self).__init__()

    def get_options(self):
        return [Option('src_name', nargs='*')]

    def run(self, src_name=None):
        try:
            for i in src_name:
                q = ProblemSource.query.filter_by(name=i).exists()
                if not db.session.query(q).scalar():
                    src = ProblemSource(i)
                    db.session.add(src)
                else:
                    print('This source already exists')
            db.session.commit()
            print('Source success added')
        except Exception as e:
            print('Occurred error: ' + str(e))


class AddProblemType(Command):
    def __init__(self):
        super(AddProblemType, self).__init__()

    def get_options(self):
        return [Option('type_name', nargs='*')]

    def run(self, type_name=None):
        try:
            for i in type_name:
                q = ProblemType.query.filter_by(type=i).exists()
                if not db.session.query(q).scalar():
                    src = ProblemType(i)
                    db.session.add(src)
                else:
                    print('This type already exists')
            db.session.commit()
            print('Type success added')
        except Exception as e:
            print('Occurred error: ' + str(e))


class EditBaseStation(Command):
    def __init__(self):
        super(EditBaseStation, self).__init__()

    def get_options(self):
        return [Option('bs_id'), Option('field_value')]

    def run(self, bs_id=None, field_value=None):
        bs = None
        try:
            bs = BaseStation.query.filter_by(code=bs_id).first()
        except Exception as e:
            print(f'Cant load basestation: {str(e)}')
            return 1
        if bs:
            try:
                field, value = field_value.split('=')
                if field in bs.__dir__():
                    setattr(bs, field, value)
                    db.add(bs)
                    db.commit()
                print('Basestation successful updated')
            except Exception as e:
                print('Error occurred: ' + str(e))
        else:
            print('Basestation does not exists')


class AddUser(Command):
    def __init__(self):
        super(AddUser, self).__init__()

    def get_options(self):
        return [Option('username'), Option('pwd'), Option('email')]

    def run(self, username=None, pwd=None, email=None):
        try:
            user = models.User(username, email)
            user.set_password(pwd)
            db.session.add(user)
        except Exception as e:
            print('Occurred error: ' + str(e))
        else:
            db.session.commit()
            print('User success added')