# Adapted from https://github.com/ashley-alf/pretzel_pd
# Copyright (c) 2026 Ashley Ramos Alfaro


def tangle_points(nums):
    n = len(nums)
    matrix = [[[0,0] for i in range(n)] for j in range(2)]

    matrix[0][0] = [-1,0]
    matrix[0][-1] = [0,1]
    count = 1
    direction = -1
    strand = 0 
    current_cell = (0,0)
    pretzel_index = 0 
    temp_num = -1

    while count < 2*n: 
        num_crossings = nums[pretzel_index]
        #print(num_crossings)
        temp_num += direction * abs(num_crossings) #get the number we gonna add
        #print(temp_num)
        if num_crossings % 2 != 0: 
            strand = (strand+1)%2
        current_cell = ((current_cell[0]+1)%2,current_cell[1])

        #we want to check if the position we want to update has been filled out already or nah:
        if matrix[current_cell[0]][current_cell[1]][strand] != 0: #if this is true then we are at a cycle
            #find the nearest 0 and update current cell to that
            if temp_num > 0:
                temp_num *= -1 
            
            #could be done more efficiently just wanted to see if it worked
            finish = False
            for i in range(len(matrix[0])): 
                # if matrix[0][i][0] == 0: 
                #     current_cell = (0,i)
                #     strand = 0
                #     pretzel_index = current_cell[1]
                #     direction *= -1
                #     break
                # if matrix[0][i][1] == 0: 
                #     current_cell = (0,i)
                #     strand = 1
                #     pretzel_index = current_cell[1]
                #     direction *= -1
                #     break
                if finish: 
                    break
                for s in range(2):
                    if matrix[0][i][s] == 0: 
                        current_cell = (0,i)
                        strand = s
                        pretzel_index = current_cell[1]
                        direction *= -1
                        finish = True
                        break
                
            #num_crossings = nums[pretzel_index]
            matrix[current_cell[0]][current_cell[1]][strand] = temp_num
            if strand == 0: 
                temp_cell = (current_cell[0], (current_cell[1]-1)%n)
            else: 
                temp_cell = (current_cell[0], (current_cell[1]+1)%n) 
            matrix[temp_cell[0]][temp_cell[1]][(strand+1)%2] = temp_num*-1
            count +=1
            continue
        
        matrix[current_cell[0]][current_cell[1]][strand] = temp_num #add whatever the number is
        #now add the same number to it's corresponding place: 
        #looking for where to go next
        if strand == 0: 
            current_cell = (current_cell[0], (current_cell[1]-1)%n)
        else: 
            current_cell = (current_cell[0], (current_cell[1]+1)%n)        
       
        #update these
        
        pretzel_index = current_cell[1]
       
        strand = (strand+1)%2
        direction *= -1
        #get temp num
        temp_num *= -1
        matrix[current_cell[0]][current_cell[1]][strand] = temp_num
        count += 1
    # for i in range(len(matrix)):
    #     print(matrix[i])
    return [[tuple(sublist) for sublist in inner_list] for inner_list in matrix]
# tangle_points([3,4,-2,1])


def get_pd(temp, new, slope, direction, strand): 
    if slope < 0: 
        if direction == -1 and strand == 1: 
            return [abs(temp[1]), abs(temp[0]), abs(new[0]), abs(new[1])]
        elif direction == 1 and strand == 0: 
            return [abs(temp[0]), abs(temp[1]), abs(new[1]), abs(new[0])]
    else: 
        if direction == -1 and strand == 0: 
            return [abs(temp[0]), abs(new[0]), abs(new[1]), abs(temp[1])]
        elif direction == 1 and strand == 1: 
            return [abs(temp[1]), abs(new[1]), abs(new[0]), abs(temp[0])]
    return None


def valid_labeling_2(start_cell, end_cell, pretzel,strand, direction): 
    #return none if it is or else strand of which label is bad
    (a,b) = start_cell
    (c,d) = end_cell
    left_strand_from_start = True
    right_strand_from_start = True
    pair_1 = 0
    pair_2 = 0
    if pretzel % 2 == 0: 
        #check directions: 
        pair_1 = (a,c)
        pair_2 = (b,d)
        if a < 0: # we going down so check if c it is bigger 
           
            if abs(c) < abs(a): # if it's not then make it False
                left_strand_from_start = False 
        else: #if going up u wanna check c is smaller
            if abs(a) < abs(c): 
                left_strand_from_start = False 
        if b <0: # we going down so check if c it is bigger 
            pair_2 = (b,d)
            if abs(d) < abs(b): # if it's not then make it False
                right_strand_from_start = False 
        else: #if going up u wanna check c is smaller
            if abs(b) < abs(d): 
                right_strand_from_start = False 
    else: #we are at an even: 
         #check directions: 
        pair_1 = (a,d)
        pair_2 = (b,c)
        if a < 0: # we going down so check if d it is bigger 
            if abs(a) < abs(d): # if it's not then make it False
                l_strand_from_start = False 
        else: #if going up u wanna check d is smaller
            if abs(d) < abs(a): 
                left_strand_from_start = False 
        if b <0: # we going down so check if c it is bigger 
            if abs(b) < abs(c): # if it's not then make it False
                right_strand_from_start = False 
        else: #if going up u wanna check c is smaller
            if abs(c) < abs(b): 
                right_strand_from_start = False 

    if (left_strand_from_start and right_strand_from_start) == False:
        if left_strand_from_start == False and strand == 1:
            if pair_1[0] <0:
                sign = -1
            else:
                sign = 1
            return (start_cell[1]+ direction, (abs(pair_1[1])+abs(pretzel)-1)*sign)
        elif right_strand_from_start and strand == 0: 
            if pair_2[0] <0:
                sign = -1
            else:
                sign = 1
            return ((abs(pair_2[1])+abs(pretzel)-1)*sign, start_cell[0] + direction)
    return None


def change_zero_cell(cell, pretzel, goal_cell):
    if cell[0] == 0: 
        if pretzel % 2 == 0:
            cell = (abs(goal_cell[1])+ abs(pretzel) -1, cell[1])

        else: 
            cell = (abs(goal_cell[0])+ abs(pretzel) -1, cell[1])
    elif cell[1] == 0: 
        if pretzel % 2 == 0:
            cell = (cell[0], abs(goal_cell[1])+ abs(pretzel) -1)
        else: 
            cell = (cell[0], abs(goal_cell[0])+ abs(pretzel) -1)
    return cell


def pretzel_pd_2(nums, pairs):
    total_crossings = sum([abs(num) for num in nums])
    n = len(nums)
    pd_code = []
    start_index = (0,0) 
    goal_index = (1,0)

    start_cell = pairs[start_index[0]][start_index[1]]
    goal_cell = pairs[goal_index[0]][goal_index[1]]
    explored = set()
    explored.add(-1)
    pretzel = nums[start_index[1]]
    temp_cell = start_cell
    direction = -1 
    strand = 0 
    temp_crossing = 0
    while len(pd_code) < total_crossings: 
        if temp_crossing == abs(pretzel)-1: #if the next crossing is the goal
            new_cell = (goal_cell[0], goal_cell[1])

        else: 
            new_cell = (temp_cell[1]+direction, temp_cell[0]+direction) 
            if new_cell[0] == 0 or new_cell[0] == 0: 
                new_cell = change_zero_cell(new_cell, pretzel, goal_cell)
                #print("new cell: ", new_cell)
        
        if temp_cell == start_cell: 
            if temp_cell[strand] not in explored:
                explored.add(temp_cell[strand])
            #want to check if we at a link and need to change stuff 

            if pretzel != nums[-1]:
                temp_new_cell = valid_labeling_2(start_cell, goal_cell, pretzel, strand,direction)
                if temp_new_cell!= None: 
                    #print("wow in here: ", temp_new_cell)
                    new_cell = temp_new_cell
      

        pd = get_pd(temp_cell, new_cell, pretzel, direction, strand)
        temp_crossing += 1
            
        if pd is not None: 
            pd_code.append(pd)
        temp_cell = new_cell 
        #print(f"temp_cell: {temp_cell} and goal_cell = {goal_cell} =? {temp_cell == goal_cell}")
        strand = (strand+1)%2
       
        
        if temp_cell == goal_cell: 
            if temp_cell[strand] not in explored:
                explored.add(temp_cell[strand])
            
            if strand == 1: 
                start_index = (goal_index[0], (goal_index[1]+1)%n)
                goal_index = ((start_index[0]+1)%2, start_index[1])

                start_cell = pairs[start_index[0]][start_index[1]]
                goal_cell = pairs[goal_index[0]][goal_index[1]]
            else: 
                start_index = (goal_index[0], (goal_index[1]-1)%n)
                goal_index = ((start_index[0]+1)%2, start_index[1])

                start_cell = pairs[start_index[0]][start_index[1]]
                goal_cell = pairs[goal_index[0]][goal_index[1]]
            
            temp_cell = start_cell
            strand = (strand+1)%2
            pretzel = nums[start_index[1]]
            direction *= -1
            temp_crossing = 0
            if temp_cell[strand] in explored: # means we are about to start in a cycle
                #look for strand that has not been explored yet -> could optimize later
                finish = False
                for i in range(len(pairs[0])): 
                    if finish: 
                        break
                    for s in range(2):
                        if pairs[0][i][s] not in explored:
                            start_index = (0,i)
                            goal_index = (1,i)

                            start_cell = pairs[start_index[0]][start_index[1]]
                            goal_cell = pairs[goal_index[0]][goal_index[1]]

                            strand = s
                    
                            pretzel = nums[start_index[1]]
                            
                            if pairs[0][i][s] < 0: 
                                direction = -1
                            else: 
                                direction = 1
                            
                            temp_crossing = 0
                            finish = True
                            temp_cell = start_cell
                            explored.add(temp_cell[strand])
    return pd_code
