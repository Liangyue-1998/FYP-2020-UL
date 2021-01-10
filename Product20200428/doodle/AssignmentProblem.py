import copy

MINNUM = 0
MAXNUM = float('inf')


def hungarian_method(jobs, workers, edges):
    # 匈牙利算法，逐个为job找worker匹配，如果有边，则判断该worker是被匹配，
    # 没被匹配，则进行匹配，被匹配了，则递归判断该worker所匹配的job能否移位去匹配其它woker。
    matched_dict = {}
    def match_work(job, marked):
        # 声明局部变量matched_dict 否则不能在闭包函数（函数中的函数）中修改此变量
        nonlocal matched_dict
        # 筛去 被标记的worker
        workers_ = [i for i in workers if i not in marked]
        # 筛去 和此job没边的workker
        workers_ = [i for i in workers_ if (job, i) in edges]
        for worker in workers_:
            # 标记此worker 代表这个worker已经被锁定了，在接下来的递归中，不能动这个被标记的worker。
            marked.append(worker)
            # 如果 worker被匹配了，而且与此worker匹配的job不能移位去匹配其它worker，则放过此worker，继续。
            if worker in matched_dict and not match_work(
                matched_dict[worker], marked):
                continue
            # 否则 我把worker匹配给此job（这个worker没被匹配则直接匹配，已匹配，则已通过上面调用的not match_work(matched_dict[worker], marked)移位空出匹配位）
            else:
                matched_dict[worker] = job
                return True
        return False
    
    for job in jobs:
        # 尝试为此job匹配worker，无论成败。
        match_work(job, marked=[])
    matched = [(v, k) for k, v in matched_dict.items()]
    return matched


def find_cover_lines(costs):
    # 将costs 转为 二分图形式，方便使用匈牙利法 两个点集分别为jobs和workers的索引编号
    # costs 为0的元素，添加进edges边集合，edges = [(job, worker), ...]
    edges = []
    for i in range(len(costs)):
        for j in range(len(costs[0])):
            if costs[i][j] == 0:
                edges.append((i, j))
    jobs = [i for i in range(len(costs))]
    workers = [i for i in range(len(costs[0]))]

    # 使用匈牙利法找最大匹配，matched = [(job, worker), ...]
    matched =  hungarian_method(jobs, workers, edges)
    non_matched = [i for i in edges if i not in matched]
    # 在最大匹配中的job和worker
    matched_job = [i for i, _ in matched]
    matched_worker = [i for _, i in matched]

    # 标记没有被匹配的job所在行
    marked_job_lines = [i for i in jobs if i not in matched_job]
    # 用来标记没有被匹配的worker所在列
    marked_worker_lines = []
    # 记录被标记的行和列是否已经在上一次循环中使用过
    used_job_lines = []
    used_worker_lines = []

    # 当所有被标记的行和列都被使用过，且没有新添加的行和列时候，跳出循环。
    while (marked_job_lines!=used_job_lines or 
        marked_worker_lines!=used_worker_lines):
        # step 1. mark worker line
        # 遍历标记过的行，已使用过, 则跳过,否则: 遍历所有的worker(列) 如果有未被标记的列在此行中有未匹配元素，则标记该行。
        # 上述操作完成，记该行已被使用。
        for job in marked_job_lines:
            if job in used_job_lines: continue
            for worker in workers:
                if (job, worker) in non_matched and worker not in marked_worker_lines:
                    marked_worker_lines.append(worker)
            used_job_lines.append(job)
        # step 2. mark job line
        # 遍历标记过的列，已使用过,则跳过,否则: 遍历所有的job(行) 如果有未被标记的行在此列中有已匹配元素，则标记该行。
        # 上述操作完成，记该列已被使用。
        for worker in marked_worker_lines:
            if worker in used_worker_lines: continue
            for job in jobs:
                if (job, worker) in matched and job not in marked_job_lines:
                    marked_job_lines.append(job)
            used_worker_lines.append(worker)

    # 在未标记的行和已标记的列画盖0线。
    cover_job_lines = [i for i in jobs if i not in marked_job_lines]   
    cover_worker_lines = marked_worker_lines
    return cover_job_lines, cover_worker_lines, matched


def balance_problem(costs):
    if len(costs) < len(costs[0]):
        # 行数小于列数，行补0
        diff_num = len(costs[0]) - len(costs)
        add_costs = [[0 for i in range(len(costs[0]))] for _ in range(diff_num)]
        costs += add_costs
    elif len(costs) > len(costs[0]):
        # 列数小于行数，列补0
        diff_num = len(costs) - len(costs[0])
        for i in range(len(costs)):
            costs[i].extend([0]*diff_num)
    else: pass
    return costs


def solve_assignment_problem(costs, optimize_type='minimum'):
    # history: dict 用来记录求解过程中的中间结果，用来展示步骤。
    history = {}
    history['original_costs'] = copy.deepcopy(costs)
    history['unbalance'] = 1
    history['optimize_type'] = optimize_type

    # 判断是否balance，否则调用 balance_problem() 补0
    if len(costs)==len(costs[0]): history['unbalance'] = 0
    else: costs = balance_problem(costs)
    history['balanced_costs'] = copy.deepcopy(costs)

    # 根据optimize_type替被换限制的占位符 '' 'null' 为对应的MAXNUM和MINNUM
    if optimize_type == 'maximum':
        placeholder = MINNUM
    elif optimize_type == 'minimum':
        placeholder = MAXNUM
    else: raise Exception('optimize_type error!')

    for i in range(len(costs)):
        for j in range(len(costs[0])):
            if costs[i][j] == '' or costs[i][j] == 'null':
                costs[i][j] = placeholder
            elif type(costs[i][j]) == str: raise 'placeholder error!' # 既不是 '' 'null'，还属于字符串 报错。
            else: continue
    history['transform_costs'] = copy.deepcopy(costs)

    max_value = max([max(row) for row in costs]) # 选取costs中的最大值
    if optimize_type == 'maximum':
        # 优化类型为求最大值，则用costs最大值减去所有的costs
        costs = [[max_value-j for j in i] for i in costs]
        history['subtract_max'] = copy.deepcopy(costs)
    # 每行减去行最小值，每列减去列最小值。
    # step 1. Subtract the smallest value in each row 
    costs = [[v-min(row) for v in row] for row in costs]
    history['subtract_row'] = copy.deepcopy(costs)
    # step 2. Subtract the smallest value in each column
    min_col_values = [max_value, ] * len(costs[0])
    for i in range(len(costs)):
        for j in range(len(costs[0])):
            if costs[i][j] <= min_col_values[j]:
                min_col_values[j] = costs[i][j]
    for i in range(len(costs)):
        for j in range(len(costs[0])):
            costs[i][j] -= min_col_values[j]
    history['subtract_column'] = copy.deepcopy(costs)
    
    # step 3. find zero-cover lines and juding if finish
    # 调用 find_cover_lines() 找到 盖0线，以及最大匹配。
    cover_job_lines, cover_worker_lines, matched = find_cover_lines(costs)
    history['optimize'] = []
    history['optimize'].append({'cover_job_lines': cover_job_lines.copy(), 
        'cover_worker_lines': cover_worker_lines.copy(), 'matched': matched.copy(),
         'updated_costs': [], 'update_value': 0, 'update_value_position': (),})
    # 当 盖0线数目 小于 costs行数 执行以下循环 更新costs矩阵以此增加0的数目
    while(len(cover_job_lines+cover_worker_lines)<len(costs)):
        # step 4. update costs matrix
        # 找未被覆盖元素中的最小值
        min_value = max_value
        min_value_position = (0, 0)
        for job in range(len(costs)):
            if job in cover_job_lines: continue
            for worker in range(len(costs[0])):
                if worker in cover_worker_lines: continue
                if costs[job][worker] <= min_value:
                    min_value = costs[job][worker]
                    min_value_position = (job, worker)
        # 未覆盖元素减去其最小值
        for job in range(len(costs)):
            if job in cover_job_lines: continue
            for worker in range(len(costs[0])):
                if worker in cover_worker_lines: continue
                costs[job][worker] -= min_value
        # 覆盖线交叉元素加上未覆盖元素的最小值
        for job in cover_job_lines:
            for worker in cover_worker_lines:
                costs[job][worker] += min_value
        history['optimize'][-1]['updated_costs'] = copy.deepcopy(costs)
        history['optimize'][-1]['update_value'] = min_value
        history['optimize'][-1]['update_value_position'] = min_value_position
        # 更新完毕后 再调用 find_cover_lines() 找到 盖0线，以及最大匹配。
        # 若此时 盖0线数目不再小于costs行数，则跳出循环，否则继续循环。
        cover_job_lines, cover_worker_lines, matched = find_cover_lines(costs)
        history['optimize'].append({'cover_job_lines': cover_job_lines.copy(), 
            'cover_worker_lines': cover_worker_lines.copy(), 'matched': matched.copy(), 
            'updated_costs': [], 'update_value': 0, 'update_value_position': (),})
    total_cost = sum([history['balanced_costs'][i][j] for i, j in matched])
    return total_cost, history



if __name__=="__main__":
    # costs = [
    #     [9, 11, 14, 11, 7],
    #     [6, 15, 13, 13, 10],
    #     [12, 13, 6, 8, 8],
    #     [11, 9, 10, 12, 9],
    #     [7, 12, 14, 10, 14],
    # ]
    # costs = [
    #     [3, 2, 3],
    #     [4, 7, 4],
    #     [5, 4, 6]
    # ]
    # costs = [
    #     [90, 75, 75, 80],
    #     [35, 85, 55, 65],
    #     [125, 95, 90, 105],
    #     [45, 110, 95, 115],
    # ]
    # costs = [
    #     [23, 45, 62, 34],
    #     [34, 41, 53, 54],
    #     [31, 51, 36, 26]
    # ]
    # costs = [
    #     [42, 35, 28, 21],
    #     [30, 25, 20, 15],
    #     [30, 25, 20, 15],
    #     [24, 20, 16, 12],
    # ]
    # costs = [
    #     [8, 2, 'null', 5, 4],
    #     [10, 9, 2, 8, 4],
    #     [5, 4, 9, 6, 'null'],
    #     [3, 6, 2, 8, 7],
    #     [5, 6, 10, 4, 3]
    # ]
    costs = [
        [9, 11, 15, 10, 11],
        [12, 9, 'null', 10, 9],
        ['null', 11, 14, 11, 7],
        [14, 8, 12, 7, 8]
    ]
    # costs = [
    #     [3, 2, 3],
    #     [4, 7, 4],
    #     [5, 4, 6]
    # ]
    total_cost, data = solve_assignment_problem(costs, optimize_type='minimum')
    print(total_cost)
    print(data)
    total_cost, data = solve_assignment_problem(costs, optimize_type='maximum')
    print(total_cost)
    print(data)