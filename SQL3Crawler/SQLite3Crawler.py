import os
import sys
import pathlib
import sqlite3
import datetime
import collections
import functools
import time
import xml.etree.ElementTree as ET

READ_SIGNATURE = 0
READ_FULL_FILE = 1

META_DATA_FILE = 1
DATA_FILE = 2
BOTH_FILE = META_DATA_FILE | DATA_FILE

FILE_SIGNATURE = bytes.fromhex("53 51 4c 69 74 65 20 66 6f 72 6d 61 74 20 33 00") #SQLite format 3\x00

SIGNATURE_NOT_FOUND = -1

EMPTY_STRING = ""

TYPE_NAME = 0
NAME = 1
TABLE_NAME = 2
ROOT_PAGE = 3
QUERY = 4

NEXT = 1
PREVIOUS = -1
QUIT = 0

CURRENT_PATH = 0

def decode_bytes(data, encoding="utf-8"):
  if(type(data) is bytes):
    return data.decode(encoding)
  else:
    return data

def concat(a, concatenator, b):
    return a + concatenator + b

def concat_path(base_path, file_name):
  return concat(base_path, "\\", file_name)

def convert_time(timestamp):
  epoch = datetime.datetime(1601, 1, 1)
  return epoch + datetime.timedelta(microseconds=timestamp)

def get_class_name(cls):
  return cls.__name__

def get_error_frame_info():
  errtype = sys.exc_info()[0]
  errno = sys.exc_info()[1]
  frame = sys.exc_info()[2]
  while(frame.tb_next):
    frame = frame.tb_next
  lineno = frame.tb_lineno
  current_frame = frame.tb_frame
  file_path = current_frame.f_code.co_filename
  function_name = current_frame.f_code.co_name
  return get_class_name(errtype), errno, lineno, function_name, file_path

class Dump_SQLite_Tables:
  def __init__(self):
    self.root_path = ""
    self.metadata_dump_path = ""
    self.data_dump_path = ""
    self.metadata_dump_handle = None
    self.data_dump_handle = None
    self.databases_data = collections.defaultdict(list)
    self.databases_metadata = collections.defaultdict(list)
    self.databases_file_paths = set()
    self.databases_last_file_path = ""
    self.main_config_root = None
    self.possible_roots = []
    self.root_iterator = 0
    
    self.__open_xml_parser__()
    self.set_paths(CURRENT_PATH)

  def __open_xml_parser__(self):
    if(not os.path.isfile("config.cfg")):
      raise OSError("cannot open 'config.cfg' file")
    xml_parser = ET.parse("config.cfg")
    if(xml_parser == None):
      raise ValueError("failed to parse xml file")
    self.main_config_root = xml_parser.getroot()
    if(self.main_config_root == None):
      raise ValueError("failed to get root")
    if(len(self.main_config_root) == 0):
      raise ValueError("there is no possible roots to choose")
    for possible_root in self.main_config_root:
      if(possible_root.tag == None):
        raise ValueError("empty tag is not allowed")
      if(possible_root.tag in self.possible_roots):
        raise ValueError("duplicate tags are not allowed")
      self.possible_roots.append(possible_root.tag)

  def __read_config_file__(self, entry_name):
    root = self.main_config_root.find(self.possible_roots[self.root_iterator])
    if(root == None):
      raise ValueError(f"{self.possible_roots[self.root_iterator]} root not found")
    entry_root = root.find(entry_name)
    if(entry_root == None):
      raise ValueError(f"{entry_name} root not found in xml file")
    if(entry_root.text == None):
      raise ValueError("path not found in xml file")
    return entry_root.text

  def __open_files__(self):
    metadata_base_path, metadata_dump_file_name = os.path.split(self.metadata_dump_path)
    if(not os.path.isdir(metadata_base_path)):
      print(f"INFO> new path `{metadata_base_path}` has been created.")
      pathlib.Path(metadata_base_path).mkdir(parents=True)
    data_base_path, data_dump_file_name = os.path.split(self.data_dump_path)
    if(not os.path.isdir(data_base_path)):
      print(f"INFO> new path `{data_base_path}` has been created.")
      pathlib.Path(data_base_path).mkdir(parents=True)
    self.metadata_dump_handle = open(self.metadata_dump_path, "w+")
    self.data_dump_handle = open(self.data_dump_path, "w+")

  def __close_files__(self):
    if(self.metadata_dump_handle != None):
      self.metadata_dump_handle.close()
      self.metadata_dump_handle = None
    if(self.data_dump_handle != None):
      self.data_dump_handle.close()
      self.data_dump_handle = None

  def __write_to_file__(self, file_handle, data):
    if(file_handle == None):
      raise ValueError("cannot write data to file, file_handle == None")
    if(file_handle & META_DATA_FILE):
      print(data, file=self.metadata_dump_handle)
    if(file_handle & DATA_FILE):
      print(data, file=self.data_dump_handle)

  #NOTE: mode READ_SIGNATURE - scan only for signature
  #NOTE: mode READ_FULL_FILE - scan full file
  def __check_file_signature__(self, mode, path, file_signature):
    with open(path, "rb") as file:
        return file.read(-1 if mode == READ_FULL_FILE else len(file_signature)).find(file_signature)

  def __add_database_path__(self, file_path):
    self.databases_file_paths.add(file_path)
    self.databases_last_file_path = file_path

  def __remove_database_path__(self, file_path):
    if(file_path in self.databases_file_paths):
      self.databases_file_paths.remove(file_path)
      self.databases_last_file_path = ""

  def __get_last_database_path__(self):
    if(len(self.databases_file_paths) == 0):
      raise ValueError("empty file paths set")
    if(self.databases_last_file_path == EMPTY_STRING):
      raise ValueError("empty file path")
    if(not (self.databases_last_file_path in self.databases_file_paths)):
      raise ValueError("file path not in file paths set")
    return self.databases_last_file_path

  def print_possible_roots(self):
    print("INFO> possible roots:", ", ".join(self.possible_roots))

  def print_current_paths(self):
    print(
f"""INFO>
  root          -> {self.root_path}
  metadata dump -> {self.metadata_dump_path}
  data dump     -> {self.data_dump_path}
""")

  def set_paths(self, direction):
    self.root_iterator = max(0, min(self.root_iterator + direction, len(self.possible_roots) - 1))
    self.root_path = self.__read_config_file__("root_path")
    self.metadata_dump_path = self.__read_config_file__("metadata_dump_path")
    self.data_dump_path = self.__read_config_file__("data_dump_path")
    print("INFO> paths have been set to:")
    self.print_current_paths()

  def get_paths(self):
    return (self.root_path, self.metadata_dump_path, self.data_dump_path)

  def get_all_metadata_info(self, cursor):
    LIST_METADATA_INFO_CONTENT = "SELECT * FROM sqlite_master"
    cursor.execute(LIST_METADATA_INFO_CONTENT)
    return cursor.fetchall()

  def get_all_tables(self, cursor):
    LIST_TABLE_CONTENT = "SELECT * FROM sqlite_master WHERE type='table'"
    cursor.execute(LIST_TABLE_CONTENT)
    return cursor.fetchall()

  def get_table_content(self, cursor, table_name):
    LIST_TABLE_CONTENT = f"SELECT * FROM {table_name}"
    cursor.execute(LIST_TABLE_CONTENT)
    return cursor.fetchall()

  def read_all_metadata(self):
    for file, table_meta in self.databases_metadata.items():
      print(file, table_meta)

  def read_all_data(self):
    for file, table in self.databases_data.items():
      print(file, table)

  def get_databases_data(self):
    return self.databases_data

  def get_databases_metadata(self):
    return self.databases_metadata

  def get_databases_file_paths(self):
    return self.databases_file_paths

  def get_all_metadata(self, cursor):
    for type_name, name, table_name, root_page, query in self.get_all_metadata_info(cursor):
      self.databases_metadata[self.__get_last_database_path__()].append((
        decode_bytes(type_name),
        decode_bytes(name),
        decode_bytes(table_name),
        decode_bytes(root_page),
        decode_bytes(query)
        ))

  def get_all_data(self, cursor):
    file_path = self.__get_last_database_path__()
    database_info = self.databases_metadata.get(file_path, None)
    if(database_info == None):
      raise KeyError(f"entry database_info[{file_path}] doesn't exists")
    for type_name, name, table_name, root_page, query in database_info:
      if(type_name == "table"):
        table_content = self.get_table_content(cursor, table_name)
        self.databases_data[file_path].append((table_name, table_content))

  def get_all_databases(self):
    for subdir, dirs, files in os.walk(os.path.split(self.root_path)[0]):
      for file in files:
        file_path = concat_path(subdir, file)
        try:
          if(self.__check_file_signature__(READ_SIGNATURE, file_path, FILE_SIGNATURE) != SIGNATURE_NOT_FOUND): #NOTE: we don't handle cases when offset != 0
            with sqlite3.connect(file_path) as db_connection:
              db_connection.text_factory = bytes
              cursor = db_connection.cursor()
              self.__add_database_path__(file_path)
              self.get_all_metadata(cursor)
              self.get_all_data(cursor)
              #NOTE: consider intermediate dump if dictionaries will get too big
        #TODO(SyntaX): Do better error handling
        except OSError as errno:
          self.__write_to_file__(BOTH_FILE, concat(file_path, "\n", f"ERROR> cannot open file: {errno}."))
          #NOTE: can sqlite raise OSError?
        except sqlite3.OperationalError as errno:
          self.__write_to_file__(BOTH_FILE, concat(file_path, "\n", f"ERROR> SQLite3 error: {errno}."))
          self.__remove_database_path__(file_path)
        except (ValueError, KeyError):
          errtype, errno, lineno, function_name, file_path = get_error_frame_info()
          print(f"ERROR> {errtype} value: `{errno}` in {lineno} line of `{function_name}` function in {file_path}.")
          return
        except:
          errtype, errno, lineno, function_name, file_path = get_error_frame_info()
          print(f"ERROR> unknown {errtype} value: `{errno}` in {lineno} line of `{function_name}` function in {file_path}.")
          return

  def dump_all_databases(self):
    self.clear_all_databases() #NOTE: consider that
    self.__open_files__()
    self.get_all_databases()
    for file_path, meta_data_tables in self.databases_metadata.items():
      self.__write_to_file__(META_DATA_FILE, concat(file_path, ":", EMPTY_STRING))
      for meta_data_table in meta_data_tables:
        self.__write_to_file__(META_DATA_FILE, meta_data_table)
    for file_path, data_tuple_list in self.databases_data.items():
      self.__write_to_file__(DATA_FILE, concat(file_path, ":", EMPTY_STRING))
      for data_tuple in data_tuple_list:
        table_name, data_tables = data_tuple
        self.__write_to_file__(DATA_FILE, concat(table_name, ":", EMPTY_STRING))
        for data_table in data_tables:
          self.__write_to_file__(DATA_FILE, data_table)
    self.__close_files__()

  def clear_all_databases(self):
    self.databases_data.clear()
    self.databases_metadata.clear()
    self.databases_file_paths.clear()
    self.databases_last_file_path = ""

class Program:
  def __init__(self):
    self.dump_sqlite_tables_instance = Dump_SQLite_Tables()
    self.possible_input = {
        "q": QUIT,
        "1": functools.partial(self.dump_sqlite_tables_instance.set_paths, NEXT),
        "2": functools.partial(self.dump_sqlite_tables_instance.set_paths, PREVIOUS),
        "3": self.dump_sqlite_tables_instance.print_current_paths,
        "4": self.dump_sqlite_tables_instance.dump_all_databases,
        "5": self.dump_sqlite_tables_instance.clear_all_databases,
        "6": self.dump_sqlite_tables_instance.read_all_metadata,
        "7": self.dump_sqlite_tables_instance.read_all_data,
        "8": self.__run_tests__
      }

  def __user_input_handler__(self, user_input):
    handle = self.possible_input.get(user_input, None)
    if(handle == QUIT):
      return False
    if(handle != None):
      time_begin = time.time()
      handle()
      time_end = time.time()
      print(f"INFO> query execution took: {time_end - time_begin} seconds.")
    return True

  def __run_tests__(self):
    def check_for_keys_equality():
      databases_file_paths = self.dump_sqlite_tables_instance.get_databases_file_paths()
      databases_metadata = self.dump_sqlite_tables_instance.get_databases_metadata()
      databases_data = self.dump_sqlite_tables_instance.get_databases_data()
      if(len(databases_file_paths) == len(databases_metadata) == len(databases_data)):
        return True
      else:
        file_paths_keys = databases_file_paths
        databases_metadata_keys = databases_metadata.keys()
        databases_data_keys = databases_data.keys()
        print(f"INFO> file_paths_keys len: {len(file_paths_keys)}")
        print(f"INFO> databases_metadata_keys len: {len(databases_metadata_keys)}")
        print(f"INFO> databases_data_keys len: {len(databases_data_keys)}")
        a_b_difference = set(file_paths_keys).symmetric_difference(set(databases_metadata_keys))
        b_c_difference = set(databases_metadata_keys).symmetric_difference(set(databases_data_keys))
        print(f"INFO> (file_paths_keys, databases_metadata_keys) difference: {a_b_difference}")
        print(f"INFO> (databases_metadata_keys, databases_data_keys) difference: {b_c_difference}")
        print(f"INFO> (file_paths_keys, databases_metadata_keys, databases_data_keys) difference: {a_b_difference.union(b_c_difference)}")
        return False

    def check_for_empty_content():
      databases_file_paths = self.dump_sqlite_tables_instance.get_databases_file_paths()
      databases_metadata = self.dump_sqlite_tables_instance.get_databases_metadata()
      databases_data = self.dump_sqlite_tables_instance.get_databases_data()
      for file_path in databases_file_paths:
        if(file_path == ""): break
        if(databases_metadata.get(file_path, None) == None): break #check if content exists
        if(databases_data.get(file_path, None) == None): break
      else:
        return True
      return False

    print("INFO> test `check_for_keys_equality` is running...")
    if(check_for_keys_equality()):
      print("INFO> test `check_for_keys_equality` passed.")
    else:
      print("INFO> test `check_equality_dictionaries_size` failed.")
    print("INFO> test `check_for_empty_content` is running...")
    if(check_for_empty_content()):
      print("INFO> test `check_for_empty_content` passed.")
    else:
      print("INFO> test `check_for_empty_content` failed.")

  def run(self):
    user_input = ""
    while(self.__user_input_handler__(user_input)):
      self.dump_sqlite_tables_instance.print_possible_roots()
      user_input = input(
"""choose:
  1-next root
  2-previous root
  3-current paths
  4-dump databases
  5-clear databases
  6-read metadata
  7-read data
  8-run tests
  q-quit
>>""")

if(__name__ == "__main__"):
  prog = Program()
  prog.run()
