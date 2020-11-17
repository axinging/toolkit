import os
import platform
import re
import subprocess
import sys

HOST_OS = platform.system().lower()
if HOST_OS == 'windows':
    lines = subprocess.Popen('dir %s' % __file__.replace(
        '/', '\\'), shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        match = re.search(r'\[(.*)\]', line.decode('utf-8'))
        if match:
            script_dir = os.path.dirname(match.group(1)).replace('\\', '/')
            break
    else:
        script_dir = sys.path[0]
else:
    lines = subprocess.Popen(
        'ls -l %s' % __file__, shell=True, stdout=subprocess.PIPE).stdout.readlines()
    for line in lines:
        match = re.search(r'.* -> (.*)', line.decode('utf-8'))
        if match:
            script_dir = os.path.dirname(match.group(1))
            break
    else:
        script_dir = sys.path[0]

sys.path.append(script_dir)
sys.path.append(script_dir + '/..')

from util.base import *  # pylint: disable=unused-wildcard-import

class GPUTest(Program):
    AQUARIUM_BASE = {
        Util.WINDOWS: {
            'd3d12': 33,
            'dawn_d3d12': 38,
            'dawn_vulkan': 38,
        },
        Util.LINUX: {
            'dawn_vulkan': 50,
        }
    }

    REAL_TYPE_INFO_INDEX_FILTER = 0
    REAL_TYPE_INFO_INDEX_EXTRA_ARGS = 1
    REAL_TYPE_INFO = {
        'aquarium': ['--test-time', ''],
        'gtest_angle': ['--gtest_filter', ''], # --cfi-diag=0
        'gtest_chrome': ['--gtest_filter', ''], # --cfi-diag=0
        'telemetry_gpu_integration_test': ['--test-filter', '--retry-limit 1 --retry-only-retry-on-failure-tests'],
        'webgpu_blink_web_tests': ['--isolated-script-test-filter', '--seed 4 --jobs=1 --driver-logging --no-show-results --clobber-old-results --no-retry-failures --order=natural --isolated-script-test-filter=wpt_internal/webgpu/* --ignore-default-expectations --additional-expectations=../../third_party/blink/web_tests/WebGPUExpectations --additional-driver-flag=--enable-unsafe-webgpu --additional-driver-flag=--disable-gpu-sandbox'],
    }

    VIRTUAL_NAME_INFO_INDEX_REAL_TYPE = 0
    VIRTUAL_NAME_INFO_INDEX_DRYRUN = 1
    VIRTUAL_NAME_INFO_INDEX_EXTRA_ARGS = 2
    VIRTUAL_NAME_INFO = {
        'aquarium_d3d12': ['aquarium', '1'],
        'aquarium_dawn_d3d12': ['aquarium', '1'],
        'aquarium_dawn_vulkan': ['aquarium', '1'],

        'angle_end2end_tests': ['gtest_angle', 'EGLAndroidFrameBufferTargetTest'],
        'angle_perftests': ['gtest_angle', 'BindingsBenchmark'],
        'angle_white_box_tests': ['gtest_angle', 'VulkanDescriptorSetTest.AtomicCounterReadLimitedDescriptorPool'],

        'dawn_end2end_skip_validation_tests': ['gtest_chrome', 'BindGroupTests', '--adapter-vendor-id=0x8086'],
        'dawn_end2end_tests': ['gtest_chrome', 'BindGroupTests'],
        'dawn_end2end_validation_layers_tests': ['gtest_chrome', 'BindGroupTests'],
        'dawn_end2end_wire_tests': ['gtest_chrome', 'BindGroupTests'],
        'dawn_perf_tests': ['gtest_chrome', 'BufferUploadPerf.Run/Vulkan_Intel', '--override-steps=1'],
        'gl_tests_passthrough': ['gtest_chrome', 'SharedImageFactoryTest'],
        'vulkan_tests': ['gtest_chrome', 'BasicVulkanTest'],

        'info_collection_tests': ['telemetry_gpu_integration_test', 'InfoCollection_basic'],
        'trace_test': ['telemetry_gpu_integration_test', 'TraceTest_2DCanvasWebGL'],
        'webgl2_conformance_d3d11_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl2_conformance_gl_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl2_conformance_validating_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],   # d3d11
        'webgl_conformance_d3d11_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl_conformance_d3d9_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl_conformance_gl_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl_conformance_validating_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],
        'webgl_conformance_vulkan_passthrough_tests': ['telemetry_gpu_integration_test', 'conformance/attribs'],

        'webgpu_blink_web_tests': ['webgpu_blink_web_tests', 'wpt_internal/webgpu/cts.html?q=webgpu:api,validation,setViewport:*'],
        'webgpu_blink_web_tests_with_backend_validation': ['webgpu_blink_web_tests', 'wpt_internal/webgpu/cts.html?q=webgpu:api,validation,setViewport:*'],
    }

    CHROME_CONFIG_FILES = ['chromium.gpu.fyi.json', 'chromium.dawn.json']
    CONFIG_FILE = 'config.json'

    index = 0
    TARGET_INDEX_OS = index
    index += 1
    TARGET_INDEX_PROJECT = index
    index += 1
    TARGET_INDEX_VIRTUAL_NAME = index
    index += 1
    TARGET_INDEX_REAL_NAME = index
    index += 1
    TARGET_INDEX_REAL_TYPE = index
    index += 1
    TARGET_INDEX_RUN_ARGS = index
    index += 1
    TARGET_INDEX_TOTAL_SHARDS = index
    TARGET_INDEX_MAX = index

    RESULT_FILE_PATTERN = r'^.*-(.*).log$'

    EMAIL_SENDER = 'webgraphics@intel.com'
    EMAIL_ADMIN = 'yang.gu@intel.com'
    EMAIL_TO = 'yang.gu@intel.com'

    SEPARATOR = '|'

    def __init__(self):
        parser = argparse.ArgumentParser(description='GPU Test')

        parser.add_argument('--debug', dest='debug', help='debug', action='store_true')
        parser.add_argument('--target', dest='target', help='target', default='all')
        parser.add_argument('--email', dest='email', help='email', action='store_true')
        parser.add_argument('--repeat', dest='repeat', help='repeat', type=int, default=1)

        parser.add_argument('--list', dest='list', help='list', action='store_true')
        parser.add_argument('--sync', dest='sync', help='sync', action='store_true')
        parser.add_argument('--sync-skip-mesa', dest='sync_skip_mesa', help='sync skip mesa', action='store_true')
        #parser.add_argument('--sync-skip-roll-dawn', dest='sync_skip_roll_dawn', help='sync skip roll dawn', action='store_true')
        parser.add_argument('--sync-roll-dawn', dest='sync_roll_dawn', help='sync roll dawn', action='store_true')
        parser.add_argument('--build', dest='build', help='build', action='store_true')
        parser.add_argument('--build-skip-mesa', dest='build_skip_mesa', help='build skip mesa', action='store_true')
        parser.add_argument('--run', dest='run', help='run', action='store_true')
        parser.add_argument('--dryrun', dest='dryrun', help='dryrun', action='store_true')
        parser.add_argument('--dryrun-with-shard', dest='dryrun_with_shard', help='dryrun with shard', action='store_true')
        parser.add_argument('--report', dest='report', help='report')
        parser.add_argument('--batch', dest='batch', help='batch', action='store_true')
        parser.add_argument('--mesa-rev', dest='mesa_rev', help='mesa revision', default='system')
        parser.add_argument('--mesa-type', dest='mesa_type', help='mesa type', default='iris')

        parser.epilog = '''
examples:
python %(prog)s --sync --build --run --dryrun --email
python %(prog)s --batch --dryrun
'''
        python_ver = Util.get_python_ver()
        if python_ver[0] == 3:
            super().__init__(parser)
        else:
            super(GPUTest, self).__init__(parser)

        args = self.args

        self.chromium_dir = '%s/chromium' % self.root_dir
        self.chromium_src_dir = '%s/src' % self.chromium_dir
        target_os = self.target_os
        if target_os == 'default':
            target_os = Util.HOST_OS

        self._get_targets()
        os_targets = []
        for target in self.targets:
            if target[self.TARGET_INDEX_OS] == target_os:
                os_targets.append(target)
        self.os_targets = os_targets

        target_indexes = []
        arg_target = args.target
        if arg_target == 'all':
            arg_target = '0-%d' % (len(self.os_targets) - 1)
        arg_targets = arg_target.split(',')
        for tmp_target in arg_targets:
            if '-' in tmp_target:
                tmp_targets = tmp_target.split('-')
                target_min = int(tmp_targets[0])
                target_max = int(tmp_targets[1])
                target_indexes.extend(range(target_min, target_max + 1))
            else:
                target_indexes.append(int(tmp_target))
        target_indexes = sorted(target_indexes)
        self.target_indexes = target_indexes

        if args.report:
            self.result_dir = args.report
        else:
            self.result_dir = '%s/result/%s' % (self.root_dir, self.timestamp)
            Util.ensure_dir(self.result_dir)
        self.exec_log = '%s/exec.log' % self.result_dir
        if not args.report:
            Util.ensure_nofile(self.exec_log)
        Util.append_file(self.exec_log, 'OS%s%s' % (self.SEPARATOR, Util.HOST_OS_RELEASE))

        if args.email or args.batch:
            self.email = True
        else:
            self.email = False

        for i in range(self.args.repeat):
            self._handle_ops()

    def list(self):
        for index, target in enumerate(self.os_targets):
            print('%s: %s' % (index, target[self.TARGET_INDEX_VIRTUAL_NAME]))

    def sync(self):
        all_timer = Timer()
        projects = []
        if self.target_os == Util.LINUX and not self.args.sync_skip_mesa and self.args.mesa_rev != 'system':
            projects.append('mesa')

        for target_index in self.target_indexes:
            project = self.os_targets[target_index][self.TARGET_INDEX_PROJECT]
            if project not in projects:
                projects.append(project)

        for project in projects:
            timer = Timer()
            if project == 'mesa':
                cmd = 'python %s --root-dir %s/mesa --sync' % (Util.MESA_SCRIPT, self.root_dir)
            else:
                cmd = 'python %s --root-dir %s/%s --sync --runhooks' % (Util.GNP_SCRIPT, self.root_dir, project)
            dryrun = self.args.dryrun
            if self._execute(cmd, exit_on_error=False, dryrun=dryrun)[0]:
                Util.error('Sync failed')

            if project == 'aquarium' and self.args.sync_roll_dawn:
                Util.chdir('%s/aquarium/third_party/dawn' % self.root_dir)
                self._execute('git checkout master && git pull', dryrun=dryrun)
                Util.info('Roll Dawn in Aquarium to %s on %s' % (Util.get_repo_hash(), Util.get_repo_date()))

            self._log_exec(timer.stop(), project, cmd)
        self._log_exec(all_timer.stop())

    def build(self):
        all_timer = Timer()
        projects = []
        project_targets = {}

        if self.target_os == Util.LINUX and not self.args.build_skip_mesa and self.args.mesa_rev != 'system':
            projects.append('mesa')

        for target_index in self.target_indexes:
            project = self.os_targets[target_index][self.TARGET_INDEX_PROJECT]
            real_name = self.os_targets[target_index][self.TARGET_INDEX_REAL_NAME]
            if project not in projects:
                projects.append(project)
                project_targets[project] = [real_name]
            elif real_name not in project_targets[project]:
                project_targets[project].append(real_name)

        for project in projects:
            timer = Timer()
            if project == 'mesa':
                cmd = 'python %s --root-dir %s/mesa --build' % (Util.MESA_SCRIPT, self.root_dir)
            else:
                cmd = 'python %s --no-component-build --root-dir %s/%s --makefile --build --build-target %s' % (Util.GNP_SCRIPT, self.root_dir, project, ','.join(project_targets[project]))
            if self._execute(cmd, exit_on_error=False, dryrun=self.args.dryrun)[0]:
                error_info = '[GPUTest] Project %s build failed' % project
                if self.email:
                    Util.send_email(self.EMAIL_SENDER, self.EMAIL_ADMIN, error_info, '')
                Util.error(error_info)

            self._log_exec(timer.stop(), project, cmd)
        self._log_exec(all_timer.stop())

    def run(self):
        all_timer = Timer()
        Util.clear_proxy()

        if Util.HOST_OS == Util.LINUX and self.args.mesa_rev != 'system':
            gpu_driver = 'Mesa %s' % Util.set_mesa('%s/mesa/backup' % self.root_dir, self.args.mesa_rev, self.args.mesa_type)
            gpu_name, _ = Util.get_gpu_info()
        else:
            gpu_name, gpu_driver = Util.get_gpu_info()

        Util.append_file(self.exec_log, 'GPU name%s%s' % (self.SEPARATOR, gpu_name))
        Util.append_file(self.exec_log, 'GPU driver%s%s' % (self.SEPARATOR, gpu_driver))

        args = self.args
        logged_projects = []
        for index, target_index in enumerate(self.target_indexes):
            project = self.os_targets[target_index][self.TARGET_INDEX_PROJECT]
            if project not in logged_projects:
                if project == 'chromium':
                    rev = ChromiumRepo('%s/chromium/src' % self.root_dir).get_working_dir_rev()
                else:
                    Util.chdir('%s/%s' % (self.root_dir, project))
                    rev = Util.get_repo_rev()
                logged_projects.append(project)
                info = '%s Revision%s%s' % (project.capitalize(), self.SEPARATOR, rev)
                Util.append_file(self.exec_log, info)
            virtual_name = self.os_targets[target_index][self.TARGET_INDEX_VIRTUAL_NAME]
            if Util.HOST_OS == Util.WINDOWS and virtual_name in ['dawn_end2end_validation_layers_tests']:
                continue

            real_name = self.os_targets[target_index][self.TARGET_INDEX_REAL_NAME]
            real_type = self.os_targets[target_index][self.TARGET_INDEX_REAL_TYPE]
            config_cmd = 'python %s --run --root-dir %s/%s --run-target %s --run-rev out' % (Util.GNP_SCRIPT, self.root_dir, project, real_name)

            run_args = self.os_targets[target_index][self.TARGET_INDEX_RUN_ARGS]
            for i, run_arg in reversed(list(enumerate(run_args))):
                if run_arg.startswith('--extra-browser-args'):
                    run_arg = run_arg.replace('--extra-browser-args=', '')
                    run_args[i] = '--extra-browser-args=\\\"%s --disable-backgrounding-occluded-windows\\\"' % run_arg
                elif run_arg == '--browser=release_x64':
                    run_args[i] = '--browser=release'
                elif run_arg.startswith('--gtest-benchmark-name'):
                    run_args.remove(run_arg)
                elif run_arg in ['-v', '--show-stdout', 'angle_end2end_tests', 'angle_perftests', '--print-test-stdout']:
                    run_args.remove(run_arg)
                elif run_arg == '--target=Release_x64':
                    run_args[i] = '--target=release'
                # we use 5912 and 3e98 in test
                elif run_arg == '3e92':
                    run_args += ['--expected-device-id', '3e98']
            config_args = ' '.join(run_args)

            real_type_extra_args = self.REAL_TYPE_INFO[real_type][self.REAL_TYPE_INFO_INDEX_EXTRA_ARGS]
            if real_type_extra_args:
                config_args += ' %s' % real_type_extra_args
            if len(self.VIRTUAL_NAME_INFO[virtual_name]) > self.VIRTUAL_NAME_INFO_INDEX_EXTRA_ARGS:
                virtual_name_extra_args = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_EXTRA_ARGS]
                if virtual_name_extra_args:
                    config_args += ' %s' % virtual_name_extra_args

            dryrun_cond = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_DRYRUN]
            if args.dryrun and dryrun_cond:
                if real_type not in ['aquarium', 'webgpu_blink_web_tests']:
                    dryrun_cond = '*%s*' % dryrun_cond
                config_args += ' %s=%s' % (self.REAL_TYPE_INFO[real_type][self.REAL_TYPE_INFO_INDEX_FILTER], dryrun_cond)

            if real_type in ['telemetry_gpu_integration_test', 'webgpu_blink_web_tests']:
                total_shards_arg = '--total-shards'
                shard_index_arg = '--shard-index'
                output_arg = '--write-full-results-to'
            elif real_type in ['gtest_chrome']:
                output_arg = '--test-launcher-summary-output'

            total_shards = int(self.os_targets[target_index][self.TARGET_INDEX_TOTAL_SHARDS])
            if real_type in ['gtest_angle', 'gtest_chrome']:
                total_shards = 1

            for shard_index in range(total_shards):
                shard_args = ''
                if total_shards > 1:
                    shard_args += ' %s=%s %s=%s' % (total_shards_arg, total_shards, shard_index_arg, shard_index)

                total_target_indexes = len(self.target_indexes)
                total_target_indexes_str = str(total_target_indexes)
                total_target_indexes_str_len = len(total_target_indexes_str)
                total_shards_str = str(total_shards)
                total_shards_str_len = len(total_shards_str)
                op = 'index%s-shard%s-%s' % (str(index).zfill(total_target_indexes_str_len), str(shard_index).zfill(total_shards_str_len), virtual_name)
                result_file = '%s/%s.log' % (self.result_dir, op)

                if real_type in ['aquarium']:
                    shard_args += ' > %s' % result_file
                elif real_type in ['telemetry_gpu_integration_test', 'webgpu_blink_web_tests', 'gtest_chrome']:
                    shard_args += ' %s=%s' % (output_arg, result_file)
                    Util.ensure_file(result_file)

                cmd = '%s --run-args="%s%s"' % (config_cmd, config_args, shard_args)
                timer = Timer()
                self._execute(cmd, exit_on_error=False)
                self._log_exec(timer.stop(), op, cmd)

                if real_type in ['gtest_angle']:
                    output_file = '%s/chromium/src/out/release/output.json' % self.root_dir
                    if os.path.exists(output_file):
                        shutil.move(output_file, result_file)
                    else:
                        Util.ensure_file(result_file)
                self._parse_result(result_file, verbose=True)
                if args.dryrun and not args.dryrun_with_shard:
                    break

        self._log_exec(all_timer.stop())
        self.report()

    def batch(self):
        self.sync()
        self.build()
        self.run()

    def report(self):
        html = '''
<head>
  <meta http-equiv="content-type" content="text/html; charset=windows-1252">
  <style type="text/css">
    table {
      border: 2px solid black;
      border-collapse: collapse;
      border-spacing: 0;
      text-align: left;
    }
    table tr td {
      border: 1px solid black;
    }
  </style>
</head>
<body>
  <h2>Overall</h2>
    <ul>'''
        for line in open(self.exec_log):
            fields = line.rstrip('\n').split(self.SEPARATOR)
            name = fields[0]
            if not re.match('sync|build|run', name, re.I):
                html += '''
      <li>%s: %s</li>''' % (name, fields[1])
        html += '''
      <li>Report: %s</li>''' % self.timestamp
        html += '''
    </ul>
  <h2>Details</h2>
  <table>
    <tr>
      <td><strong>Name</strong>  </td>
      <td><strong>Time</strong></td>
      <td><strong>PASS_FAIL</strong></td>
      <td><strong>FAIL_PASS</strong></td>
      <td><strong>FAIL_FAIL</strong></td>
      <td><strong>PASS_PASS</strong></td>
    </tr>'''

        total_regressions = 0
        for line in open(self.exec_log):
            fields = line.split(self.SEPARATOR)
            name = fields[0]
            if re.match('sync|build', name, re.I):
                time = fields[1]
                pass_fail_info = fail_pass_info = fail_fail_info = pass_pass_info = ''
            elif re.match('run', name, re.I):
                op = name[4:]
                result_file = '%s/%s.log' % (self.result_dir, op)
                pass_fail, fail_pass, fail_fail, pass_pass_len = self._parse_result(result_file)
                total_regressions += len(pass_fail)
                time = fields[1]
                pass_fail_info = '%s<p>%s' % (len(pass_fail), '<p>'.join(pass_fail[:10]))
                fail_pass_info = '%s<p>%s' % (len(fail_pass), '<p>'.join(fail_pass[:10]))
                fail_fail_info = len(fail_fail)
                pass_pass_info = pass_pass_len
            else:
                continue

            html += '''
    <tr>
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
      <td>%s</td>
    </tr>''' % (name, time, pass_fail_info, fail_pass_info, fail_fail_info, pass_pass_info)

        html += '''
  </table>
</body>'''
        report_file = '%s/report.html' % self.result_dir
        Util.ensure_nofile(report_file)
        Util.append_file(report_file, html)
        subject = '[GPUTest] Host %s Datetime %s Regressions %s' % (Util.HOST_NAME, self.timestamp, total_regressions)

        if self.email:
            Util.send_email(self.EMAIL_SENDER, self.EMAIL_TO, subject, html, type='html')

    def _get_targets(self):
        targets = []
        recorded_os_virtual_name = []
        if self.args.debug:
            recorded_virtual_name = []

        for config_file in self.CHROME_CONFIG_FILES:
            configs = Util.load_json('%s/testing/buildbot/%s' % (self.chromium_src_dir, config_file))
            for config in configs:
                if not re.search('Intel', config):
                    continue

                if re.search('Linux', config):
                    target_os = Util.LINUX
                elif re.search('Win10', config):
                    target_os = Util.WINDOWS
                else:
                    continue

                if self.args.debug:
                    Util.debug(config)

                target_types = configs[config]
                for target_type in target_types:
                    for target_detail in target_types[target_type]:
                        if 'name' in target_detail:
                            tmp_name = target_detail['name']
                        else:
                            tmp_name = ''
                        if 'test' in target_detail:
                            tmp_test = target_detail['test']
                        else:
                            tmp_test = ''
                        if 'isolate_name' in target_detail:
                            tmp_isolate_name = target_detail['isolate_name']
                        else:
                            tmp_isolate_name = ''

                        virtual_name = tmp_name or tmp_test
                        real_name = tmp_isolate_name or tmp_test or tmp_name

                        if virtual_name not in self.VIRTUAL_NAME_INFO.keys():
                            continue

                        if self.args.debug:
                            Util.debug(virtual_name)

                        if self.args.debug and virtual_name not in recorded_virtual_name:
                            recorded_name.append(virtual_name)

                        if [target_os, virtual_name] in recorded_os_virtual_name:
                            continue
                        else:
                            recorded_os_virtual_name.append([target_os, virtual_name])

                        # init
                        target = [0] * (self.TARGET_INDEX_MAX + 1)
                        target[self.TARGET_INDEX_TOTAL_SHARDS] = 1
                        target[self.TARGET_INDEX_OS] = target_os
                        target[self.TARGET_INDEX_VIRTUAL_NAME] = virtual_name
                        target[self.TARGET_INDEX_PROJECT] = 'chromium'
                        target[self.TARGET_INDEX_REAL_NAME] = real_name
                        target[self.TARGET_INDEX_REAL_TYPE] = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_REAL_TYPE]
                        if 'args' in target_detail:
                            target_run_args = target_detail['args']

                        target[self.TARGET_INDEX_RUN_ARGS] = target_run_args
                        if 'swarming' in target_detail and 'shards' in target_detail['swarming']:
                            target[self.TARGET_INDEX_TOTAL_SHARDS] = target_detail['swarming']['shards']

                        targets.append(target)

        # aquarium
        os_backends = {
            'windows': ['d3d12', 'dawn_d3d12', 'dawn_vulkan'],
            'linux': ['dawn_vulkan']
        }
        for os in os_backends:
            for backend in os_backends[os]:
                targets.append([os, 'aquarium', 'aquarium_%s' % backend, 'aquarium', 'aquarium', ['--test-time 30', '--num-fish 30000', '--enable-msaa', '--turn-off-vsync', '--integrated-gpu', '--window-size=1920,1080', '--print-log', '--backend %s' % backend], 1])

        targets = sorted(targets, key=operator.itemgetter(self.TARGET_INDEX_OS, self.TARGET_INDEX_PROJECT, self.TARGET_INDEX_REAL_TYPE, self.TARGET_INDEX_VIRTUAL_NAME))
        Util.dump_json('%s/gputest/config.json' % ScriptRepo.IGNORE_DIR, targets)
        self.targets = targets

        if self.args.debug:
            Util.debug(len(recorded_virtual_name))
            recorded_virtual_name = sorted(recorded_virtual_name)
            for virtual_name in recorded_virtual_name:
                Util.debug(virtual_name)
            for target in targets:
                Util.debug(target)

    def _log_exec(self, time, op='', cmd=''):
        if op:
            info = '%s %s' % (inspect.stack()[1][3].capitalize(), op)
        else:
            info = 'Total %s' % inspect.stack()[1][3].capitalize()
        info += '%s%s' % (self.SEPARATOR, time)
        if cmd:
            info += '%s%s' % (self.SEPARATOR, cmd)
        Util.info(info)
        Util.append_file(self.exec_log, info)

    def _parse_result(self, result_file, verbose=False):
        file_name = os.path.basename(result_file)
        op = file_name.replace('.log', '')
        match = re.search(self.RESULT_FILE_PATTERN, file_name)
        virtual_name = match.group(1)

        real_type = self.VIRTUAL_NAME_INFO[virtual_name][self.VIRTUAL_NAME_INFO_INDEX_REAL_TYPE]

        if real_type == 'aquarium':
            pass_pass = []
            pass_fail = []
            fail_pass = []
            fail_fail = []
            lines = open(result_file).readlines()
            for line in lines:
                match = re.match('Avg FPS: (.*)', line)
                if match:
                    run_fps = int(match.group(1))
                    backend = virtual_name.replace('aquarium_', '')
                    base_fps = self.AQUARIUM_BASE[Util.HOST_OS][backend]
                    if run_fps < base_fps:
                        pass_fail.append('%s -> %s' % (base_fps, run_fps))
                    else:
                        pass_pass.append('%s -> %s' % (base_fps, run_fps))
                    break

            pass_pass_len = len(pass_pass)

        else:
            if real_type in ['gtest_chrome']:
                type = real_type
            elif real_type in ['gtest_angle', 'telemetry_gpu_integration_test', 'webgpu_blink_web_tests']:
                type = 'gtest_angle'
            pass_fail, fail_pass, fail_fail, pass_pass_len = Util.get_test_result(result_file, type)

        return pass_fail, fail_pass, fail_fail, pass_pass_len

    def _handle_ops(self):
        args = self.args
        if args.list:
            self.list()
        if args.sync:
            self.sync()
        if args.build:
            self.build()
        if args.run:
            self.run()
        if args.batch:
            self.batch()
        if args.report:
            self.report()

if __name__ == '__main__':
    GPUTest()