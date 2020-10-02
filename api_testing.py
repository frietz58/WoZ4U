import qi
import threading
import time


def log_states():
    while True:
        tang_dist = motion_srv.getTangentialSecurityDistance()
        orth_dist = motion_srv.getOrthogonalSecurityDistance()
        print("tang: {}\north: {}\n".format(tang_dist, orth_dist))

        time.sleep(1)


if __name__ == "__main__":
    global qi_session
    qi_session = qi.Session()

    try:
        qi_session.connect(str("tcp://" + "130.239.182.11" + ":" + "9559"))
    except RuntimeError as msg:
        print("qi session connect error!:")
        print(msg)

    global motion_srv
    motion_srv = qi_session.service("ALMotion")
    motion_srv.setTangentialSecurityDistance(0.3)
    motion_srv.setOrthogonalSecurityDistance(0.3)

    log_thread = threading.Thread(target=log_states)
    log_thread.start()

    time.sleep(5)
    print("Setting Tangential Security distance")
    motion_srv.setTangentialSecurityDistance(0.4)
    # lmao, the bug is in the API (v2.5), not my code >.<
    # If we INCREASE the tangential collision avoidance distance, the orthogonal one is adjusted as well...
    # TODO: Test whether this happens in 2.8 as well and maybe open issue

    time.sleep(10)
