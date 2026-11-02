# ══════════════════════════════════════════════════════════════
# PAGE: ATTENDANCE
# ══════════════════════════════════════════════════════════════


elif page == "Attendance":
    st.markdown("""
    <div class="app-header">
        <h1>Attendance Tracker</h1>
        <p>Track lectures by timetable and view attendance analytics.</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = 1
    
    # Academic Year Selection
    ay_result = api_call("GET", f"/attendance/academic-years/{user_id}")
    academic_years = ay_result.get("academic_years", []) if ay_result else []
    if not academic_years:
        academic_years = ["2025-2026"]
    selected_ay = st.selectbox("Academic Year", options=academic_years)
    
    st.markdown("---")
    
    # Today's Overview Dashboard
    st.markdown("### Today's Overview")
    today_data = api_call("GET", f"/attendance/today/{user_id}")
    if today_data:
        tstats = today_data.get("stats", {})
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Lectures", tstats.get("total", 0))
        c2.metric("Attended", tstats.get("present", 0))
        c3.metric("Missed", tstats.get("absent", 0))
        c4.metric("Not Marked", tstats.get("not_marked", 0))
        c5.metric("Attendance %", f"{tstats.get('percentage', 0)}%")
        
        st.progress(min(tstats.get("percentage", 0) / 100, 1.0))
        
        # Today's Present vs Absent graph
        if tstats.get("total", 0) > 0:
            import pandas as pd
            chart_data = pd.DataFrame({
                "Status": ["Present", "Absent", "Not Marked"],
                "Count": [tstats.get("present", 0), tstats.get("absent", 0), tstats.get("not_marked", 0)]
            })
            st.bar_chart(chart_data.set_index("Status"))
    else:
        st.info("No schedule available for today.")
    
    st.markdown("---")
    
    # Today's Lecture Schedule and Attendance
    st.markdown("### Today's Lectures")
    if today_data and today_data.get("lectures"):
        for idx, lec in enumerate(today_data["lectures"]):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.write(f"**{lec['subject_name']}**")
            with col2:
                st.write(f"{lec['start_time']} - {lec['end_time']}")
            with col3:
                status = lec.get("attendance_status", "not_marked")
                if status == "present":
                    st.success("Present")
                elif status == "absent":
                    st.error("Absent")
                else:
                    st.warning("Not Marked")
            with col4:
                if lec.get("attendance_id"):
                    # Allow editing
                    new_status = st.selectbox(
                        "Update",
                        ["present", "absent"],
                        key=f"upd_{lec['attendance_id']}_{idx}",
                        label_visibility="collapsed"
                    )
                    if st.button("Update", key=f"updb_{lec['attendance_id']}_{idx}"):
                        res = api_call("PUT", f"/attendance/update/{lec['attendance_id']}", json={"status": new_status})
                        if res:
                            st.rerun()
                else:
                    c_a, c_b = st.columns(2)
                    with c_a:
                        if st.button("Present", key=f"p_{idx}"):
                            res = api_call("POST", "/attendance/mark-lecture", json={
                                "user_id": user_id,
                                "subject_id": lec["subject_id"],
                                "lecture_date": today_data["date"],
                                "start_time": lec["start_time"],
                                "end_time": lec["end_time"],
                                "lecture_name": lec["lecture_name"],
                                "status": "present"
                            })
                            if res:
                                st.rerun()
                    with c_b:
                        if st.button("Absent", key=f"a_{idx}"):
                            res = api_call("POST", "/attendance/mark-lecture", json={
                                "user_id": user_id,
                                "subject_id": lec["subject_id"],
                                "lecture_date": today_data["date"],
                                "start_time": lec["start_time"],
                                "end_time": lec["end_time"],
                                "lecture_name": lec["lecture_name"],
                                "status": "absent"
                            })
                            if res:
                                st.rerun()
    else:
        st.info("No lectures scheduled for today.")
    
    st.markdown("---")
    
    # Weekly Timetable Management
    st.markdown("### Weekly Timetable Management")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    selected_day = st.selectbox("Select Day", days)
    
    col_t1, col_t2, col_t3, col_t4 = st.columns([2, 1, 1, 1])
    subjects_list = get_subjects(user_id=user_id)
    with col_t1:
        if subjects_list:
            subj_opts = {s["name"]: s["id"] for s in subjects_list}
            sel_subj_name = st.selectbox("Subject", list(subj_opts.keys()))
            sel_subj_id = subj_opts[sel_subj_name]
        else:
            st.warning("Add subjects first")
            sel_subj_id = None
    with col_t2:
        start_t = st.time_input("Start Time")
    with col_t3:
        end_t = st.time_input("End Time")
    with col_t4:
        st.write("")
        st.write("")
        if st.button("Add Lecture") and sel_subj_id:
            res = api_call("POST", "/attendance/timetable", json={
                "user_id": user_id,
                "subject_id": sel_subj_id,
                "day_of_week": selected_day,
                "start_time": start_t.strftime("%H:%M"),
                "end_time": end_t.strftime("%H:%M"),
                "lecture_name": sel_subj_name
            })
            if res:
                st.rerun()
    
    # Show timetable for selected day
    tt_data = api_call("GET", f"/attendance/timetable/{user_id}?day_of_week={selected_day}")
    if tt_data and tt_data.get("timetable"):
        for entry in tt_data["timetable"]:
            col_d1, col_d2, col_d3, col_d4 = st.columns([2, 2, 1, 1])
            with col_d1:
                st.write(entry["subject_name"])
            with col_d2:
                st.write(f"{entry['start_time']} - {entry['end_time']}")
            with col_d3:
                st.write(entry.get("lecture_name", ""))
            with col_d4:
                if st.button("Delete", key=f"del_tt_{entry['id']}"):
                    res = api_call("DELETE", f"/attendance/timetable/{entry['id']}")
                    if res:
                        st.rerun()
    else:
        st.info(f"No lectures scheduled for {selected_day}.")
    
    st.markdown("---")
    
    # Subject-wise Attendance Analytics
    st.markdown("### Subject-wise Attendance")
    subj_analytics = api_call("GET", f"/attendance/analytics/subject-wise/{user_id}?academic_year={selected_ay}")
    if subj_analytics and subj_analytics.get("subjects"):
        for s in subj_analytics["subjects"]:
            col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns([2, 1, 1, 1, 1])
            with col_s1:
                st.write(f"**{s['subject_name']}**")
                if s.get("below_75"):
                    st.caption("Below 75%")
            with col_s2:
                st.write(f"Total: {s['total_lectures']}")
            with col_s3:
                st.write(f"Present: {s['present']}")
            with col_s4:
                st.write(f"Absent: {s['absent']}")
            with col_s5:
                st.metric("Percentage", f"{s['percentage']}%")
    else:
        st.info("No attendance data for subjects.")
    
    st.markdown("---")
    
    # Overall Attendance and Monthly Trends
    st.markdown("### Overall Attendance")
    overall = api_call("GET", f"/attendance/analytics/overall/{user_id}?academic_year={selected_ay}")
    if overall:
        c_o1, c_o2, c_o3, c_o4 = st.columns(4)
        c_o1.metric("Total Lectures", overall.get("total_lectures", 0))
        c_o2.metric("Attended", overall.get("present", 0))
        c_o3.metric("Missed", overall.get("absent", 0))
        c_o4.metric("Overall %", f"{overall.get('percentage', 0)}%")
        st.progress(min(overall.get("percentage", 0) / 100, 1.0))
    
    st.markdown("### Monthly Attendance Trends")
    monthly = api_call("GET", f"/attendance/analytics/monthly/{user_id}?academic_year={selected_ay}")
    if monthly and monthly.get("monthly"):
        import pandas as pd
        df = pd.DataFrame(monthly["monthly"])
        if not df.empty:
            st.bar_chart(df.set_index("month")[["present", "absent"]])
            st.dataframe(df)
    else:
        st.info("No monthly data available.")
    
    st.markdown("---")
    st.caption("Academic year records are preserved. Previous years can be viewed via the selector above.")
