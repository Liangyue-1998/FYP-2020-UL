from django.shortcuts import render, HttpResponse, redirect, reverse
from .AssignmentProblem import solve_assignment_problem

from django.contrib.auth.decorators import login_required
from .models import Project

import json
import itertools
from pprint import pprint
import copy


@login_required()
def index(request):
    if request.user.is_authenticated:
        projs = Project.objects.filter(user=request.user, is_save=True, is_delete=False)
    else:
        projs = None
    return render(request, 'doodle/index.html', {'projs': projs})


@login_required()
def page2(request):
    return render(request, 'doodle/page2.html')


@login_required()
def page3(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        job = int(request.POST.get('job'))
        worker = int(request.POST.get('worker'))
        proj = Project.objects.create(user=request.user, title=title, job=job, worker=worker)

        return render(request, 'doodle/page3.html', {
            'job_range': range(job),
            'worker_range': range(worker),
            'proj': proj
        })
    return render(request, 'doodle/page3.html')


def page4(request):
    return render(request, 'doodle/page4.html')


@login_required()
def parse(request):
    if request.method == "POST":
        if 'maximum' in request.POST:
            method_type = 'maximum'
        else:
            method_type = 'minimum'

        pid = request.POST.get('pid')
        proj = Project.objects.get(pk=int(pid))

        # print(request.POST)
        costs = []

        for w in range(proj.worker):
            tmp = []
            for j in range(proj.job):
                tid = "worker-{}-job-{}".format(w, j)
                # print(tid, request.POST.get(tid))
                val = request.POST.get(tid)
                if val == "" or val == "null":
                    val = "null"
                else:
                    val = int(val)
                tmp.append(val)
            costs.append(tmp)

        origin_costs = copy.deepcopy(costs)

        # save obj
        costs_data = json.dumps(costs)
        proj.data = costs_data
        proj.save()

        # print('before: ', costs)
        total_cost, data = solve_assignment_problem(origin_costs, optimize_type=method_type)
        origin_costs = data['original_costs']
        # print('after: ', costs)
        pprint(data)

        if data['optimize'][-1]:
            matched = data['optimize'][-1]['matched']
        else:
            matched = None

        return render(request, 'doodle/parse_result.html', {
            'costs': costs,
            'result': total_cost,
            'job_range': range(proj.job),
            'worker_range': range(proj.worker),
            'method': method_type,
            'project': proj,
            'matched': matched, ##坐标
            'zipcosts': zip(costs, matched),
            'origin_costs': origin_costs
        })
    return HttpResponse('up')


@login_required()
def project_parse(request, pid, method_type):
    proj = Project.objects.get(pk=pid)
    costs = json.loads(proj.data)

    total_cost, data = solve_assignment_problem(costs, optimize_type=method_type)
    origin_costs = data['original_costs']

    if data['optimize'][-1]:
        matched = data['optimize'][-1]['matched']
    else:
        matched = None

    return render(request, 'doodle/parse_result.html', {
        'costs': costs,
        'result': total_cost,
        'job_range': range(proj.job),
        'worker_range': range(proj.worker),
        'method': method_type,
        'project': proj,
        'matched': matched,
        'origin_costs': origin_costs
    })


@login_required()
def project_detail(request, pid):
    proj = Project.objects.get(pk=pid)
    costs = json.loads(proj.data)

    return render(request, 'doodle/project_detail.html', {
        'costs': costs,
        'job_range': range(proj.job),
        'worker_range': range(proj.worker),
        'project': proj,
    })


@login_required()
def save_project(request):
    if request.method == "POST":
        pid = request.POST.get('pid')
        obj = Project.objects.get(pk=pid)
        obj.is_save = True
        obj.save()
    return redirect('/')


@login_required()
def principle(request):
    return render(request, 'Principle.html')


def project_delete(request, pid):
    proj = Project.objects.get(pk=pid)
    proj.is_delete = True
    proj.save()
    return redirect('/')


@login_required()
def bin(request):
    projs = Project.objects.filter(user=request.user, is_delete=True)
    return render(request, 'doodle/bin.html', {'projs': projs})


def gen_steps(steps, optimize_list, costs, deter_n, draw_line_n, test_n, origin_costs, data):
    """
    :param steps: 前面的 steps
    :param optimize_list:
    :param costs: 最终的结果
    :param deter_n: determin 那一行的序号
    :param draw_line_n:  序号
    :param test_n: 序号
    :return:
    """
    sub_column_data = get_data_from_key('subtract_column', data)

    step_count = len(steps)
    for dt in optimize_list[:-1]:
        n = dt['update_value']
        update_costs = dt['updated_costs']
        update_value_position = dt['update_value_position']

        steps.append([DRAW_LINES.format(step_count + 1), sub_column_data, gen_template_path_from('DRAW_LINES')])
        steps.append([TEST_FOR_OPTIMALITY.format(step_count + 2, 5), None, gen_template_path_from('TEST_FOR_OPTIMALITY')])
        steps.append([DETERMINE.format(step_count + 3, n, 3), sub_column_data, gen_template_path_from('DETERMINE')])
        steps.append([SUBTRCT_THIS_ENTRY.format(step_count + 4, n, n, draw_line_n), update_costs, gen_template_path_from('SUBTRCT_THIS_ENTRY')])
        sub_column_data = update_costs

    steps.append([DRAW_LINES.format(step_count + 1), sub_column_data, gen_template_path_from('DRAW_LINES')])
    steps.append([TEST_END.format(step_count + 2), origin_costs, gen_template_path_from('FINAL')])
    return steps


def gen_highlight_elements(matched, optimize_list, steps, job, worker):
    """
    :return: 需要高亮的 td_id
    """
    update_value_positions = []
    update_value_positions_with_table = []

    lines = []  # 处理高亮的数据
    for dt in optimize_list[:-1]:
        job_lines = dt['cover_job_lines']
        worker_lines = dt['cover_worker_lines']
        lines.append((job_lines, worker_lines))

        update_value_position = dt['update_value_position']
        update_value_positions.append(update_value_position)
    lines.append((optimize_list[-1]['cover_job_lines'], optimize_list[-1]['cover_worker_lines']))

    # 处理 update_value_positions_with_table 的高亮
    count = 0
    for idx, stp in enumerate(steps):
        if 'Determine the smallest entry' in stp[0]:
            table_id = idx + 1
            update_value_positions_with_table.append("{}-{}-{}".format(
                table_id,
                update_value_positions[count][0],
                update_value_positions[count][1]
            ))
            count += 1

    lines_dict = {}
    count = 0
    for idx, stp in enumerate(steps):
        if 'Draw lines' in stp[0]:
            table_id = idx + 1
            lines_dict[table_id] = {}
            print(lines, count)
            lines_dict[table_id]['job_lines'] = lines[count][0]
            lines_dict[table_id]['worker_lines'] = lines[count][1]
            count += 1
            if count == len(lines):
                break

    ## 根据 job 过滤
    mmline = range(max([job, worker]))
    job_eles = set()
    for k, v in lines_dict.items():
        table = k
        job_lines = v['job_lines']
        for job_l in job_lines:
            for w in mmline:
                current_id = "{}-{}-{}".format(table, job_l, w)
                job_eles.add(current_id)

    # 根据 work 过滤
    worker_eles = set()
    for k, v in lines_dict.items():
        table = k
        worker_lines = v['worker_lines']
        for w in worker_lines:
            for j in mmline:
                current_id = "{}-{}-{}".format(table, j, w)
                worker_eles.add(current_id)

    # 最后一组的高亮
    lasts = set()
    table_id = len(steps)
    for j, w in matched:
        cid = "{}-{}-{}".format(table_id, j, w)
        lasts.add(cid)
    return job_eles, worker_eles, lasts, update_value_positions_with_table

# steps
STEP_SMALL_SUBTRACT_ROW = "Step {}. Subtract the smallest entry in each row from all the entries of the row."
STEP_SMALL_SUBTRACT_COLUMN = "Step {}. Subtract the smallest entry in each column from all the entries of the column."
DRAW_LINES = "Step {}. Draw lines though appropriate rows and columns so that all the zero entries of the cost matrix are covered and the minimum number of such lines is used. "
TEST_FOR_OPTIMALITY = "Step {}. Test for Optimality\n" \
                      "(1) If the minimum number of covering lines is n, an optimal assignment of zeros is possible and it finishes\n" \
                      "(2) If the minimum number of covering lines is less than lines or columns of the table, an optimal is not yet possible. In that case, proceed to step {}."
DETERMINE = "Step {}. Determine the smallest entry not covered by any line. It is {}."
HERE_MAX = "Step {}. Here the problem is of Maximization type and convert it into minimization by subtract it from maximum value."
HERE_GIVE = "Step {}. Here given problem is unbalanced and add new column/row to convert it into a balance."
THE_PO_IN = "Step {}. The position of restrictions is regarded as infinity."
THE_PO_ZE = "Step {}. The position of restrictions is regarded as zero."
SUBTRCT_THIS_ENTRY = "Step {}: Subtract {} from each uncovered elements, then add {} at intervals of crossing horizontal and vertical lines. Return to Step {}."
TEST_END = "Step {}. Test for Optimality\n" \
                      "(1) If the minimum number of covering lines is n, an optimal assignment of zeros is possible and it finishes\n"


def get_data_from_key(key, data):
    if key in data:
        sub_row_data = data[key]
    else:
        sub_row_data = []
    return sub_row_data


def gen_template_path_from(name):
    """生成路径，后面 include"""
    return "theory_html_templates/{}.html".format(name.lower())


@login_required()
def show_working(request, pid, method_type):
    is_theory = False
    if request.GET.get('theory'):
        is_theory = True

    is_detail = False
    if request.GET.get('detail'):
        is_detail = True

    proj = Project.objects.get(pk=pid)
    costs = json.loads(proj.data)
    # print(costs)
    has_null = False
    for i in itertools.chain(*costs):
        if i == float('Inf') or i == 'null':
            has_null = True
            break

    total_cost, data = solve_assignment_problem(costs, optimize_type=method_type)
    origin_costs = data['original_costs']
    pprint(data)

    if data['optimize'][-1]:
        matched = data['optimize'][-1]['matched']
    else:
        matched = None

    # show working
    job = proj.job
    worker = proj.worker


    optimize_list = data['optimize']

    sub_row_data = get_data_from_key('subtract_row', data)
    sub_column_data = get_data_from_key('subtract_column', data)
    sub_max_data = get_data_from_key('subtract_max', data)
    balanced_costs_data = get_data_from_key('balanced_costs', data)
    transform_costs_data = get_data_from_key('transform_costs', data)

    #
    eles = []
    lasts = []
    steps = []

    start_count = 1
    if has_null:
        if job == worker:
            if method_type == 'minimum':
                print('case5')
                steps = [
                    [THE_PO_IN.format(start_count), transform_costs_data, gen_template_path_from('THE_PO_IN')],
                    [STEP_SMALL_SUBTRACT_ROW.format(start_count + 1), sub_row_data, gen_template_path_from('STEP_SMALL_SUBTRACT_ROW')],
                    [STEP_SMALL_SUBTRACT_COLUMN.format(start_count + 2), sub_column_data, gen_template_path_from('STEP_SMALL_SUBTRACT_COLUMN')],
                    # [DRAW_LINES.format(start_count + 3), sub_column_data, gen_template_path_from('DRAW_LINES')],
                    # [TEST_FOR_OPTIMALITY.format(start_count + 4, start_count + 5), None, gen_template_path_from('TEST_FOR_OPTIMALITY')]
                ]

                # steps
                steps = gen_steps(steps, optimize_list, costs, deter_n=len(steps) + 1, draw_line_n=4, test_n=5, origin_costs=origin_costs, data=data)
            else:
                print('case7')
                #case7
                steps = [
                    [THE_PO_ZE.format(start_count), transform_costs_data, gen_template_path_from('THE_PO_ZE')],
                    [STEP_SMALL_SUBTRACT_COLUMN.format(start_count + 1), sub_column_data, gen_template_path_from('STEP_SMALL_SUBTRACT_COLUMN')],
                    # [DRAW_LINES.format(start_count + 4), sub_column_data, gen_template_path_from('DRAW_LINES')],
                    # [TEST_FOR_OPTIMALITY.format(start_count + 5, start_count + 6), None, gen_template_path_from('TEST_FOR_OPTIMALITY')]
                ]

                # steps
                steps = gen_steps(steps, optimize_list, costs, deter_n=len(steps) + 1, draw_line_n=5, test_n=6, origin_costs=origin_costs, data=data)
        else:
            #case 6
            if method_type == 'minimum':
                print('case6')
                steps = [
                    [HERE_GIVE.format(start_count), balanced_costs_data, gen_template_path_from('HERE_GIVE')],
                    [THE_PO_IN.format(start_count + 1), transform_costs_data, gen_template_path_from('THE_PO_IN')],
                    [STEP_SMALL_SUBTRACT_ROW.format(start_count + 2), sub_row_data, gen_template_path_from('STEP_SMALL_SUBTRACT_ROW')],
                    [STEP_SMALL_SUBTRACT_COLUMN.format(start_count + 3), sub_column_data, gen_template_path_from('STEP_SMALL_SUBTRACT_COLUMN')],
                    # [DRAW_LINES.format(start_count + 4), sub_column_data, gen_template_path_from('DRAW_LINES')],
                    # [TEST_FOR_OPTIMALITY.format(start_count + 5, start_count + 6), None, gen_template_path_from('TEST_FOR_OPTIMALITY')]
                ]
                steps = gen_steps(steps, optimize_list, costs, deter_n=len(steps) + 1, draw_line_n=5, test_n=6, origin_costs=origin_costs, data=data)
            else:
                print('case8')
                # case8
                steps = [
                    [HERE_GIVE.format(start_count), balanced_costs_data, gen_template_path_from('HERE_GIVE')],
                    [THE_PO_ZE.format(start_count + 1), transform_costs_data, gen_template_path_from('THE_PO_ZE')],
                    [HERE_MAX.format(start_count + 2), sub_max_data, gen_template_path_from('HERE_MAX')],
                    [STEP_SMALL_SUBTRACT_ROW.format(start_count + 3), sub_row_data, gen_template_path_from('STEP_SMALL_SUBTRACT_ROW')],
                    [STEP_SMALL_SUBTRACT_COLUMN.format(start_count + 4), sub_column_data, gen_template_path_from('STEP_SMALL_SUBTRACT_COLUMN')],
                    # [DRAW_LINES.format(start_count + 5), sub_column_data, gen_template_path_from('DRAW_LINES')],
                    # [TEST_FOR_OPTIMALITY.format(start_count + 6, start_count + 7), None, gen_template_path_from('TEST_FOR_OPTIMALITY')]
                ]
                steps = gen_steps(steps, optimize_list, costs, deter_n=len(steps) + 1, draw_line_n=6, test_n=7, origin_costs=origin_costs, data=data)
                print(steps)
    else:
        if job == worker:
            if method_type == 'minimum':
                # case 1
                steps = [
                    [STEP_SMALL_SUBTRACT_ROW.format(start_count), sub_row_data, gen_template_path_from('STEP_SMALL_SUBTRACT_ROW')],
                    [STEP_SMALL_SUBTRACT_COLUMN.format(start_count + 1), sub_column_data, gen_template_path_from('STEP_SMALL_SUBTRACT_COLUMN')],
                    # [DRAW_LINES.format(start_count + 2), sub_column_data, gen_template_path_from('DRAW_LINES')],
                    # [TEST_FOR_OPTIMALITY.format(start_count + 3, start_count + 4), None, gen_template_path_from('TEST_FOR_OPTIMALITY')]
                ]

                # steps
                steps = gen_steps(steps, optimize_list, costs, deter_n=len(steps) + 1, draw_line_n=3, test_n=4, origin_costs=origin_costs, data=data)
            else:
                # case 2
                steps = [
                    [HERE_MAX.format(start_count), sub_max_data, gen_template_path_from('HERE_MAX')],
                    [STEP_SMALL_SUBTRACT_ROW.format(start_count + 1), sub_row_data, gen_template_path_from('STEP_SMALL_SUBTRACT_ROW')],
                    [STEP_SMALL_SUBTRACT_COLUMN.format(start_count + 2), sub_column_data, gen_template_path_from('STEP_SMALL_SUBTRACT_COLUMN')],
                    # [DRAW_LINES.format(start_count + 3), sub_column_data, gen_template_path_from('DRAW_LINES')],
                    # [TEST_FOR_OPTIMALITY.format(start_count + 4, start_count + 5), None, gen_template_path_from('TEST_FOR_OPTIMALITY')]
                ]
                # steps
                steps = gen_steps(steps, optimize_list, costs, deter_n=len(steps) + 1, draw_line_n=4, test_n=5, origin_costs=origin_costs, data=data)
        else:
            if method_type == 'minimum':
                #case 3
                steps = [
                    [HERE_GIVE.format(start_count), balanced_costs_data, gen_template_path_from('HERE_GIVE')],
                    [STEP_SMALL_SUBTRACT_ROW.format(start_count + 1), sub_row_data, gen_template_path_from('STEP_SMALL_SUBTRACT_ROW')],
                    [STEP_SMALL_SUBTRACT_COLUMN.format(start_count + 2), sub_column_data, gen_template_path_from('STEP_SMALL_SUBTRACT_COLUMN')],
                    # [DRAW_LINES.format(start_count + 3), sub_column_data, gen_template_path_from('DRAW_LINES')],
                    # [TEST_FOR_OPTIMALITY.format(start_count + 4, start_count + 5), None, gen_template_path_from('TEST_FOR_OPTIMALITY')]
                ]
                # steps
                steps = gen_steps(steps, optimize_list, costs, deter_n=len(steps) + 1, draw_line_n=4, test_n=5, origin_costs=origin_costs, data=data)
            else:
                #case 4
                steps = [
                    [HERE_GIVE.format(start_count), balanced_costs_data, gen_template_path_from('HERE_GIVE')],
                    [HERE_MAX.format(start_count + 1), sub_max_data, gen_template_path_from('HERE_MAX')],
                    [STEP_SMALL_SUBTRACT_ROW.format(start_count + 2), sub_row_data, gen_template_path_from('STEP_SMALL_SUBTRACT_ROW')],
                    [STEP_SMALL_SUBTRACT_COLUMN.format(start_count + 3), sub_column_data, gen_template_path_from('STEP_SMALL_SUBTRACT_COLUMN')],
                    # [DRAW_LINES.format(start_count + 4), sub_column_data, gen_template_path_from('DRAW_LINES')],
                    # [TEST_FOR_OPTIMALITY.format(start_count + 5, start_count + 6), None, gen_template_path_from('TEST_FOR_OPTIMALITY')]
                ]
                steps = gen_steps(steps, optimize_list, costs, deter_n=len(steps) + 1, draw_line_n=5, test_n=6,
                      origin_costs=origin_costs, data=data)
    # highlight
    job_eles, worker_eles, lasts, update_value_positions_with_table = gen_highlight_elements(matched, optimize_list, steps, job, worker)

    #
    job_eles, worker_eles = worker_eles, job_eles
    job_and_worker_eles = list(set(job_eles).intersection(set(worker_eles)))

    # 计算 bipartite 的尺寸
    assign_text_width = 80
    circle_r = 25
    column_space = 300  #两个列的间隔
    circle_space = 30
    if proj.job > proj.worker:
        height_count = proj.job
    else:
        height_count = proj.worker
    height = circle_r * 2 * height_count + (height_count - 1) * circle_space
    width = circle_r*2 + column_space + assign_text_width

    circle_height = circle_r * 2 + circle_space
    lines = []
    for w in range(proj.worker):
        for j in range(proj.job):
            x1 = circle_r * 2 + assign_text_width
            y1 = circle_r + w * circle_height
            x2 = column_space
            y2 = y1 + circle_height * j - w*(circle_height)

            x3 = x1 + (x2-x1)/5
            y3 = y1 + (y2-y1)/5 + 5

            n = origin_costs[w][j]
            if str(n).isdigit():
                lines.append((x1, y1, x2, y2, n, x3, y3))
    print('lines', lines)

    bipartitle = {
        'circle_r': circle_r,
        'height': height,
        'width': width,
        'circle_height': circle_height,
        'column_space': column_space,
        'assign_text_width': assign_text_width,
        'lines': lines,
    }

    return render(request, 'doodle/show_working.html', {
        'origin_costs': origin_costs,
        'costs': costs,
        'result': total_cost,
        'job_range': range(proj.job),
        'worker_range': range(proj.worker),
        'method': method_type,
        'project': proj,
        'matched': matched,
        'steps': steps,
        # 'eles': list(eles),
        'job_eles': list(job_eles),
        'worker_eles': list(worker_eles),
        'lasts': list(lasts),
        'update_value_positions_with_table': update_value_positions_with_table,
        'job_and_worker_eles': job_and_worker_eles,
        'is_theory': is_theory,
        'is_detail': is_detail,
        'bipartite': bipartitle
    })


def project_rename(request, pid):
    project = Project.objects.get(pk=pid)

    if request.method == "POST":
        project.title = request.POST.get('title')
        print(request.POST)
        project.save()
        return redirect('/')
    else:
        return render(request, 'doodle/project_rename.html', {
            'project': project
        })


def project_edit(request, pid):
    project = Project.objects.get(pk=pid)

    if request.method == "POST":
        costs = []

        for w in range(project.worker):
            tmp = []
            for j in range(project.job):
                tid = "worker-{}-job-{}".format(w, j)
                val = request.POST.get(tid)
                if val == "" or val == "null":
                    val = "null"
                else:
                    val = int(val)
                tmp.append(val)
            costs.append(tmp)

        # save obj
        costs_data = json.dumps(costs)
        project.data = costs_data
        project.save()
        return redirect(reverse('project_detail', args=[project.pk]))
    else:
        return render(request, 'doodle/project_edit.html', {
            'job_range': range(project.job),
            'worker_range': range(project.worker),
            'proj': project,
            'data': json.loads(project.data)
        })


def project_reset(request, pid):
    project = Project.objects.get(pk=pid)

    data = []
    for w in range(project.worker):
        row = []
        for j in range(project.job):
            row.append(0)
        data.append(row)
    project.data = json.dumps(data)
    project.save()
    return redirect(reverse('project_edit', args=[project.pk]))


from django.core.mail import send_mail
from django.conf import settings

def email(request):
    # subject = 'Welcome to assignment problem website'
    subject = 'problem is the subject title'
    message = '好个鬼哦，有没有看新闻'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['2307905085@qq.com',]
    send_mail(
        subject=subject,
        message=message,
        from_email=email_from,
        recipient_list=recipient_list,
        fail_silently=False
    )
    return HttpResponse('OK')
